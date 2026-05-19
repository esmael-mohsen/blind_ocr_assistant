"""Evidence-based tuning recommendation helpers for Phase 10."""

from __future__ import annotations

from collections import defaultdict

from modules.benchmark.benchmark_models import (
    BenchmarkResult,
    FailureCategory,
    LanguageLabel,
    ResultStatus,
    TuningRecommendation,
    TuningTargetArea,
)


def generate_tuning_recommendations(
    run_id: str,
    results: list[BenchmarkResult],
) -> list[TuningRecommendation]:
    """Create evidence-only tuning recommendations from benchmark outcomes."""

    recommendations: list[TuningRecommendation] = []
    rejected = [item for item in results if item.failure_category is FailureCategory.IMAGE_REJECTED]
    weak = [
        item
        for item in results
        if item.failure_category in {FailureCategory.WEAK_OCR_RESULT, FailureCategory.NO_TEXT_DETECTED}
    ]
    slow_or_failed = [
        item
        for item in results
        if item.failure_category in {FailureCategory.PATH_TIMEOUT, FailureCategory.UNEXPECTED_FAILURE}
    ]
    if rejected:
        recommendations.append(
            _recommendation(
                run_id,
                "rec-image-quality",
                TuningTargetArea.IMAGE_QUALITY,
                rejected,
                "Rejected-image results indicate capture thresholds may need review.",
                "May reduce unnecessary recapture prompts for affected scenarios.",
                results,
            )
        )
    if weak:
        recommendations.append(
            _recommendation(
                run_id,
                "rec-ocr-quality",
                TuningTargetArea.OCR_QUALITY,
                weak,
                "Weak/no-text OCR outcomes indicate quality threshold or preprocessing review.",
                "May improve fallback routing before speaking low-confidence text.",
                results,
            )
        )
    if slow_or_failed:
        recommendations.append(
            _recommendation(
                run_id,
                "rec-frame-selection",
                TuningTargetArea.FRAME_SELECTION,
                slow_or_failed,
                "Timeout or unexpected failures indicate route/frame selection needs review.",
                "May reduce slow or failed OCR attempts on constrained hardware.",
                results,
            )
        )
    return recommendations


def can_accept_recommendation(
    recommendation: TuningRecommendation,
    baseline_results: list[BenchmarkResult],
    candidate_results: list[BenchmarkResult],
) -> bool:
    """Return whether measured evidence satisfies acceptance gates."""

    if not recommendation.evidence_summary.strip():
        return False
    if "tradeoff" not in recommendation.regression_risk.lower() and "risk" not in recommendation.regression_risk.lower():
        return False
    for language in (LanguageLabel.ARABIC, LanguageLabel.ENGLISH, LanguageLabel.MIXED):
        if _normal_language_regressed(language, baseline_results, candidate_results):
            return False
    return True


def _recommendation(
    run_id: str,
    recommendation_id: str,
    target_area: TuningTargetArea,
    evidence: list[BenchmarkResult],
    evidence_summary: str,
    expected_benefit: str,
    all_results: list[BenchmarkResult],
) -> TuningRecommendation:
    scenarios = sorted({label for result in evidence for label in result.scenario_labels})
    evidence_ids = tuple(f"{result.sample_id}:{result.ocr_path}" for result in evidence)
    normal_success = _normal_language_success_counts(all_results)
    risk = (
        "Regression risk/tradeoff: do not accept until normal Arabic, English, "
        f"and mixed samples remain stable. Current normal successes: {normal_success}."
    )
    return TuningRecommendation(
        recommendation_id=recommendation_id,
        run_id=run_id,
        target_area=target_area,
        affected_scenarios=tuple(scenarios),
        evidence_summary=f"{evidence_summary} Evidence count: {len(evidence)}.",
        expected_benefit=expected_benefit,
        regression_risk=risk,
        accepted=False,
        evidence_result_ids=evidence_ids,
    )


def _normal_language_success_counts(results: list[BenchmarkResult]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for result in results:
        if (
            result.language_label
            in {LanguageLabel.ARABIC, LanguageLabel.ENGLISH, LanguageLabel.MIXED}
            and "normal_quality" in result.scenario_labels
            and result.status is ResultStatus.SUCCESS
        ):
            counts[result.language_label.value] += 1
    return dict(counts)


def _normal_language_regressed(
    language: LanguageLabel,
    baseline_results: list[BenchmarkResult],
    candidate_results: list[BenchmarkResult],
) -> bool:
    baseline = _best_normal_language_score(language, baseline_results)
    candidate = _best_normal_language_score(language, candidate_results)
    return candidate < baseline


def _best_normal_language_score(language: LanguageLabel, results: list[BenchmarkResult]) -> float:
    scores = [
        result.expected_match_score if result.expected_match_score is not None else 0.0
        for result in results
        if result.language_label is language
        and "normal_quality" in result.scenario_labels
        and result.status is ResultStatus.SUCCESS
    ]
    return max(scores or [0.0])


__all__ = ["can_accept_recommendation", "generate_tuning_recommendations"]
