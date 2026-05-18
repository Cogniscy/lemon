import pytest

from lemon_factor.factors.schema import FactorComponent, FactorDecomposition
from lemon_factor.metrics.factor import asymmetric_cover, factor_sim


def dec(term, comps):
    return FactorDecomposition(
        term=term,
        components=[FactorComponent(factor=f, role=r, weight=w) for f, r, w in comps],
    )


def test_factor_sim_full_overlap():
    left = dec("UCVA", [("visual_function", "type", 0.5), ("measurement", "measure", 0.5)])
    right = dec(
        "uncorrected visual acuity",
        [("visual_function", "type", 0.5), ("measurement", "measure", 0.5)],
    )
    assert factor_sim(left, right) == pytest.approx(1.0)


def test_factor_sim_partial_overlap():
    myopia = dec(
        "myopia",
        [("disease", "type", 0.3), ("visual_system", "domain", 0.3), ("refractive_error", "type", 0.4)],
    )
    cataract = dec(
        "cataract",
        [("disease", "type", 0.3), ("visual_system", "domain", 0.3), ("lens_opacity", "type", 0.4)],
    )
    assert factor_sim(myopia, cataract) == pytest.approx(0.6)


def test_asymmetric_cover_differs_from_symmetric_similarity():
    specific = dec("myopia", [("disease", "type", 0.2), ("visual_system", "domain", 0.2), ("refractive_error", "type", 0.6)])
    generic = dec("eye disease", [("disease", "type", 0.1), ("visual_system", "domain", 0.1)])
    assert asymmetric_cover(specific, generic) == pytest.approx(0.2)
    assert factor_sim(specific, generic) == pytest.approx(0.2)
    assert asymmetric_cover(generic, specific) == pytest.approx(1.0)


def test_role_aware_factor_sim_penalizes_role_swap():
    treats = dec("TREATS(drug,disease)", [("chemical", "subject_domain", 0.4), ("disease", "object_domain", 0.4), ("treatment", "predicate_meaning", 0.2)])
    reversed_treats = dec("TREATS(disease,drug)", [("chemical", "object_domain", 0.4), ("disease", "subject_domain", 0.4), ("treatment", "predicate_meaning", 0.2)])
    assert factor_sim(treats, reversed_treats, role_aware=False) == pytest.approx(1.0)
    assert factor_sim(treats, reversed_treats, role_aware=True) == pytest.approx(0.2)
