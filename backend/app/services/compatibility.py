import json

from app.core.database import get_connection
from app.schemas.image import RasterMetadata


def row_to_metadata(row):
    return RasterMetadata(
        image_id=row["image_id"],
        filename=row["filename"],
        modality=row["modality"],
        width=row["width"],
        height=row["height"],
        bands=row["bands"],
        dtype=row["dtype"],
        crs=row["crs"],
        resolution_x=row["resolution_x"],
        resolution_y=row["resolution_y"],
        bounds=json.loads(row["bounds"]),
        transform=json.loads(row["transform"]),
        file_size_bytes=row["file_size_bytes"]
    )


def bounds_overlap(bounds_a, bounds_b):
    """
    Check whether two bounding boxes overlap.

    Bounds format:
    [left, bottom, right, top]
    """

    left_a, bottom_a, right_a, top_a = bounds_a
    left_b, bottom_b, right_b, top_b = bounds_b

    return not (
        right_a <= left_b
        or right_b <= left_a
        or top_a <= bottom_b
        or top_b <= bottom_a
    )


def check_resolution(rows, tolerance=0.10):
    """
    Check whether raster resolutions are reasonably compatible.

    tolerance=0.10 means resolutions may differ by up to 10%.
    """

    resolutions = []

    for row in rows:
        rx = row["resolution_x"]
        ry = row["resolution_y"]

        if rx is not None and ry is not None:
            resolutions.append((abs(rx), abs(ry)))

    if len(resolutions) < 2:
        return True

    reference_x, reference_y = resolutions[0]

    for current_x, current_y in resolutions[1:]:

        if reference_x == 0 or reference_y == 0:
            continue

        x_difference = (
            abs(current_x - reference_x)
            / reference_x
        )

        y_difference = (
            abs(current_y - reference_y)
            / reference_y
        )

        if (
            x_difference > tolerance
            or y_difference > tolerance
        ):
            return False

    return True


def check_grid_alignment(rows):
    """
    Check whether raster transforms use the same
    pixel grid origin and resolution.
    """

    if len(rows) < 2:
        return True

    transforms = [
        json.loads(row["transform"])
        for row in rows
    ]

    reference = transforms[0]

    # Affine transform:
    # [a, b, c, d, e, f]
    #
    # a/e -> pixel size
    # c/f -> origin

    for transform in transforms[1:]:

        if len(transform) != 6:
            return False

        if len(reference) != 6:
            return False

        # Compare pixel size and origin
        for index in [0, 2, 4, 5]:

            if abs(
                transform[index]
                - reference[index]
            ) > 1e-9:

                return False

    return True


def check_compatibility(
    image_ids: list[str],
    check_type: str
):
    connection = get_connection()

    placeholders = ",".join(
        ["?"] * len(image_ids)
    )

    rows = connection.execute(
        f"""
        SELECT *
        FROM images
        WHERE image_id IN ({placeholders})
        """,
        image_ids
    ).fetchall()

    connection.close()

    # -----------------------------
    # 1. Check that all images exist
    # -----------------------------

    found_ids = {
        row["image_id"]
        for row in rows
    }

    missing_ids = [
        image_id
        for image_id in image_ids
        if image_id not in found_ids
    ]

    if missing_ids:

        return {
            "compatible": False,
            "reasons": [
                f"Image not found: {image_id}"
                for image_id in missing_ids
            ],
            "images": [
                row_to_metadata(row)
                for row in rows
            ]
        }

    reasons = []

    # -----------------------------
    # 2. Check modality
    # -----------------------------

    modalities = [
        row["modality"]
        for row in rows
    ]

    if check_type == "optical_sar":

        optical_count = sum(
            modality in {
                "optical",
                "multispectral"
            }
            for modality in modalities
        )

        sar_count = modalities.count("sar")

        if optical_count != 1 or sar_count != 1:

            reasons.append(
                "Optical/multispectral + SAR requires "
                "exactly one optical or multispectral "
                "image and one SAR image."
            )

    elif check_type == "temporal":

        if len(rows) != 2:

            reasons.append(
                "Temporal compatibility requires "
                "exactly two images."
            )

        if len(set(modalities)) != 1:

            reasons.append(
                "Temporal images must use the "
                "same modality."
            )

    # -----------------------------
    # 3. Check CRS
    # -----------------------------

    crs_values = [
        row["crs"]
        for row in rows
    ]

    if len(set(crs_values)) > 1:

        reasons.append(
            "Images use different coordinate "
            "reference systems (CRS)."
        )

    # -----------------------------
    # 4. Check spatial overlap
    # -----------------------------

    if len(rows) >= 2:

        reference_bounds = json.loads(
            rows[0]["bounds"]
        )

        for row in rows[1:]:

            current_bounds = json.loads(
                row["bounds"]
            )

            if not bounds_overlap(
                reference_bounds,
                current_bounds
            ):

                reasons.append(
                    "Images do not have spatial overlap."
                )

                break

    # -----------------------------
    # 5. Check resolution
    # -----------------------------

    if not check_resolution(rows):

        reasons.append(
            "Image resolutions differ by more "
            "than the allowed 10% tolerance."
        )

    # -----------------------------
    # 6. Check pixel-grid alignment
    # -----------------------------

    if not check_grid_alignment(rows):

        reasons.append(
            "Images are not aligned to the same "
            "pixel grid."
        )

    # -----------------------------
    # 7. Check dimensions
    # -----------------------------

    dimensions = {
        (row["width"], row["height"])
        for row in rows
    }

    if len(dimensions) > 1:

        reasons.append(
            "Images have different raster dimensions."
        )

    # -----------------------------
    # 8. Convert rows to metadata
    # -----------------------------

    metadata_list = [
        row_to_metadata(row)
        for row in rows
    ]

    # -----------------------------
    # 9. Final result
    # -----------------------------

    return {
        "compatible": len(reasons) == 0,
        "reasons": reasons,
        "images": metadata_list
    }