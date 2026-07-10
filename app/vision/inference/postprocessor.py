import torch

from app.vision.inference.mappers import to_detection_dtos


def postprocess(
    outputs,
    processor,
    image_size: tuple[int, int],
    id2label: dict[int, str],
    confidence_threshold: float,
):
    target_sizes = torch.tensor([image_size[::-1]])
    results = processor.post_process_object_detection(
        outputs, target_sizes=target_sizes, threshold=confidence_threshold
    )[0]

    return to_detection_dtos(
        results["scores"],
        results["labels"],
        results["boxes"],
        id2label,
    )
