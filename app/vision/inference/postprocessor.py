import torch

from app.vision.inference.schemas import Detection


def postprocess(
    outputs,
    processor,
    image_size: tuple[int, int],
    id2label: dict[int, str],
    confidence_threshold: float,
) -> list[Detection]:
    target_sizes = torch.tensor([image_size[::-1]])
    results = processor.post_process_object_detection(
        outputs, target_sizes=target_sizes, threshold=confidence_threshold
    )[0]

    detections = []
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        detections.append(
            Detection(
                label=id2label[label.item()],
                confidence=score.item(),
                box=box.tolist(),
            )
        )
    return detections
