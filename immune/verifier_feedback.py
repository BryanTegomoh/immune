"""Feedback producer for a trusted host-side test harness, never the agent itself."""
from .learning import signature


def verified_feedback(record, check, key, *, critical=False, checkpoint=None):
    """Sign only when an independent postcondition fails before and passes after.

    `check` is host-owned code such as a unit test or a deterministic schema check.
    Do not load a validator, expected answer, or signing key from model output.
    The trustworthiness of the oracle remains the operator's responsibility.
    """
    if check(record['observed_output']) or not check(record['corrected_output']):
        raise ValueError('A verified failure and a successful correction are both required.')
    if not isinstance(key, str) or len(key) < 32:
        raise ValueError('Use a verifier signing key of at least 32 characters.')
    # Only trusted host arguments can attach criticality/checkpoint metadata.
    # Never sign agent-supplied control flags or self-asserted provenance.
    value = {name: record[name] for name in ('id', 'group', 'input', 'observed_output', 'corrected_output')}
    value['verified_success'] = True
    if critical:
        if not isinstance(checkpoint, str) or not checkpoint:
            raise ValueError('A critical report must identify its evaluated checkpoint.')
        value.update(critical_regression=True, checkpoint=checkpoint)
    return {'record': value, 'signature': signature(value, key)}
