from __future__ import annotations

from dataclasses import dataclass, field

from tarjamaprep.types import CleanStats


@dataclass
class ReportSection:
    """One labeled block in a clean report (one input file or one run)."""
    label: str
    total: int
    kept: int
    drop_reasons: dict[str, int] = field(default_factory=dict)
    # Extra drop buckets from steps outside the filter chain (e.g. malformed
    # lines rejected during parsing, pairs dropped by cross-file dedup).
    # They are added to the aggregate drop-reason block.
    extra_drops: dict[str, int] = field(default_factory=dict)


def section_from_stats(stats: CleanStats, label: str = "") -> ReportSection:
    return ReportSection(
        label=label,
        total=stats.total,
        kept=stats.kept,
        drop_reasons=dict(stats.drop_reasons),
    )


def format_clean_report(
    sections: list[ReportSection],
    combined_total: int | None = None,
) -> str:
    if not sections:
        return ""

    multi = len(sections) > 1
    name_w = max((len(s.label) for s in sections), default=0)
    name_w = max(name_w, len("COMBINED (post-dedup)") if combined_total is not None else 0,
                 len("FILE" if multi else "INPUT"), len("TOTAL"))

    hdr = (f"{'FILE' if multi else 'INPUT':<{name_w}}  "
           f"{'TOTAL':>10}  {'KEPT':>10}  {'DROPPED':>10}  {'KEEP%':>7}")
    out = ["=" * len(hdr), "REPORT", "=" * len(hdr), hdr, "-" * len(hdr)]

    tot_total = tot_kept = 0
    reasons_total: dict[str, int] = {}
    extras_total: dict[str, int] = {}

    for s in sections:
        dropped = s.total - s.kept
        pct = (s.kept / s.total * 100.0) if s.total else 0.0
        out.append(f"{s.label:<{name_w}}  {s.total:>10,}  {s.kept:>10,}  "
                   f"{dropped:>10,}  {pct:>6.2f}%")
        tot_total += s.total
        tot_kept += s.kept
        for k, v in s.drop_reasons.items():
            reasons_total[k] = reasons_total.get(k, 0) + v
        for k, v in s.extra_drops.items():
            extras_total[k] = extras_total.get(k, 0) + v

    if multi:
        out.append("-" * len(hdr))
        dropped = tot_total - tot_kept
        pct = (tot_kept / tot_total * 100.0) if tot_total else 0.0
        out.append(f"{'TOTAL':<{name_w}}  {tot_total:>10,}  {tot_kept:>10,}  "
                   f"{dropped:>10,}  {pct:>6.2f}%")

    if combined_total is not None:
        out.append(f"{'COMBINED (post-dedup)':<{name_w}}  "
                   f"{'':>10}  {combined_total:>10,}")

    all_reasons = dict(reasons_total)
    for k, v in extras_total.items():
        if v:
            all_reasons[k] = all_reasons.get(k, 0) + v

    out.append("")
    out.append("DROP REASONS" + (" (aggregated)" if multi else ""))
    out.append("-" * 40)
    if not all_reasons:
        out.append("  (none)")
    else:
        reason_w = max(len(r) for r in all_reasons)
        tot = sum(all_reasons.values()) or 1
        for reason, count in sorted(all_reasons.items(), key=lambda x: -x[1]):
            share = count / tot * 100.0
            out.append(f"  {reason:<{reason_w}}  {count:>10,}  {share:>6.2f}%")
    out.append("=" * len(hdr))

    return "\n".join(out)


def print_clean_report(
    sections: list[ReportSection],
    combined_total: int | None = None,
) -> None:
    text = format_clean_report(sections, combined_total)
    if text:
        print(text)
