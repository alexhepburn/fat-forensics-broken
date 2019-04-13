"""
Tests  plotting functions.
"""
# Author: Alex Hepburn <ah13558@bristol.ac.uk>
# License: new BSD

import importlib
import pytest
import sys

import numpy as np

import fatf

from fatf.transparency.lime import Lime
from fatf.utils.models import KNN
from fatf.exceptions import IncompatibleModelError, IncorrectShapeError

import fatf.utils.testing.imports as futi

NUMERICAL_ARRAY = np.array(
        [[0, 0, 0.08, 0.69],
        [1, 0, 0.03, 0.29],
        [0, 1, 0.99, 0.82],
        [2, 1, 0.73, 0.48],
        [1, 0, 0.36, 0.89],
        [0, 1, 0.07, 0.21]])
SAMPLE = np.array([0, 1, 0.08, 0.54])
STRUCT_SAMPLE = np.array([(0, 1, 0.08, 0.54)], dtype=[('a', 'i'), ('b', 'i'),
                                                      ('c', 'f'), ('d', 'f')])
PREDICTOR = KNN()
PREDICTOR.fit(NUMERICAL_ARRAY, np.array([2, 0, 1, 1, 0, 2]))
CLASS_NAMES = ['class0', 'class1', 'class2']
FEATURE_NAMES = ['feat0', 'feat1', 'feat2', 'feat3']


class InvalidModel(object):
    """
    An invalid model class -- it does not implement a ``predict_proba`` method.
    """
    def __init__(self):
        """
        Invalid initialisation.
        """
        pass

    def fit(self, X, y):
        """
        Invalid fit.
        """
        return X, y

    def predict(self, X):
        """
        Invalid predict.
        """
        return X


def test_import_when_missing():
    """
    Tests importing :mod:`fatf.transparency.Lime` module with lime_ missing.
    .. lime: https://github.com/marcotcr/lime
    """
    assert 'fatf.transparency.lime' in sys.modules
    warning_msg = (
        'Lime package is not installed on your system. You must install it in '
        'order to use the fatf.transparency.lime module. One possibility is '
        'to install LIME alongside this package with: pip install fatf[lime].')
    with futi.module_import_tester('lime', when_missing=True):
        with pytest.warns(ImportWarning) as w:
            importlib.reload(fatf.transparency.lime)
        assert len(w) == 1
        assert str(w[0].message) == warning_msg
    assert 'fatf.transparency.lime' in sys.modules


def is_explain_equal(dict1, dict2):
    """
    Small functions to test if the two dictionarys are equal to certain
    accuracy (due to float numbers). Assume dicts are returned from
    Lime.explain_instance method.
    """
    equal = True
    for key, val in dict1.items():
        if key in dict2:
            val2 = dict2[key]
            if set([x[0] for x in val]) != set([x[0] for x in val2]):
                equal = False
                break
            array1 = np.array([x[1] for x in val])
            array2 = np.array([x[1] for x in val2])
            if not np.isclose(array1, array2, atol=1e-1).all():
                equal = False
                break
        else:
            equal = False
            break
    return equal


def test_lime_exceptions():
    # Test Exceptions
    fatf.setup_random_seed()
    notimplemeneted_msg = 'LIME does not support non-numerical arrays.'
    incompatible_msg = ('LIME requires model object to have method '
                       'predict_proba().')
    shape_msg = 'data must be 2-D array.'
    cat_indices_msg = ('Indices given in categorical_indices not valid for '
                       'input array data')
    class_msg = 'Number of class names given does not correspond to model'
    feature_msg = ('Number of feature names given does not correspond to '
                   'input array')
    class_explain_msg = 'Class [10] not in dataset specified'
    with pytest.raises(ValueError) as exin:
        lime = Lime(np.ones((6, 4), dtype='U4'), PREDICTOR,
                    class_names=CLASS_NAMES, feature_names=FEATURE_NAMES)
    assert str(exin.value) == notimplemeneted_msg
    invalid_model = InvalidModel()
    with pytest.raises(IncompatibleModelError) as exin:
        lime = Lime(NUMERICAL_ARRAY, invalid_model, class_names=CLASS_NAMES,
                    feature_names=FEATURE_NAMES)
    assert str(exin.value) == incompatible_msg
    with pytest.raises(IncorrectShapeError) as exin:
        lime = Lime(np.ones((6, 4, 4)), PREDICTOR, class_names=CLASS_NAMES,
                    feature_names=FEATURE_NAMES)
    assert str(exin.value) == shape_msg
    with pytest.raises(ValueError) as exin:
        lime = Lime(NUMERICAL_ARRAY, PREDICTOR, class_names=CLASS_NAMES,
                    feature_names=FEATURE_NAMES,
                    categorical_indices=np.array([0, 10]))
    assert str(exin.value) == cat_indices_msg
#    with pytest.raises(ValueError) as exin:
#        lime = Lime(NUMERICAL_ARRAY, PREDICTOR, class_names=['class1'],
#                    feature_names=FEATURE_NAMES)
#    assert str(exin.value) == class_msg
#    with pytest.raises(ValueError) as exin:
#        lime = Lime(NUMERICAL_ARRAY, PREDICTOR, class_names=CLASS_NAMES,
#                    feature_names=['feature1'])
#    assert str(exin.value) == feature_msg
    with pytest.raises(ValueError) as exin:
        lime = Lime(NUMERICAL_ARRAY, PREDICTOR)
        exp = lime.explain_instance(SAMPLE, labels=np.array([10,]))
    assert str(exin.value) == class_explain_msg


def test_explain_instance():
    SAMPLE = np.array([0, 1, 0.08, 0.54])
    lime = Lime(NUMERICAL_ARRAY, PREDICTOR, class_names=CLASS_NAMES,
                feature_names=FEATURE_NAMES)
    explained = lime.explain_instance(SAMPLE)
    numerical_results = {
        'class0': [('feat0 <= 0.00', -0.4153762474280945),
                   ('0.50 < feat1 <= 1.00', -0.28039957101809865),
                   ('0.07 < feat2 <= 0.22', 0.03778942895340688),
                   ('0.34 < feat3 <= 0.58', -0.007232109279325609)],
        'class1': [('0.50 < feat1 <= 1.00', 0.2028506569431207),
                   ('0.07 < feat2 <= 0.22', -0.07699173494077427),
                   ('feat0 <= 0.00', 0.01986873036503522),
                   ('0.34 < feat3 <= 0.58', -0.018218096708096074)],
        'class2': [('feat0 <= 0.00', 0.39550751706305864),
                   ('0.50 < feat1 <= 1.00', 0.07754891407497788),
                   ('0.07 < feat2 <= 0.22', 0.039202305987367285),
                   ('0.34 < feat3 <= 0.58', 0.02545020598742168)]}
    assert is_explain_equal(explained, numerical_results)

    # change so feat0 and feat1 are treated as categorical
    lime = Lime(NUMERICAL_ARRAY, PREDICTOR, class_names=CLASS_NAMES,
                feature_names=FEATURE_NAMES,
                categorical_indices=np.array([0, 1]))
    explained_categorical = lime.explain_instance(SAMPLE)
    categorical_results = {
        'class0': [('feat0=0', -0.4133642307066818),
                   ('feat1=1', -0.2823750842408885),
                   ('0.07 < feat2 <= 0.22', 0.03691814698219216),
                   ('0.34 < feat3 <= 0.58', -0.007121345403493817)],
        'class1': [('feat1=1', 0.20469522417252528),
                   ('0.07 < feat2 <= 0.22', -0.07618678461871677),
                   ('feat0=0', 0.017961780673545476),
                   ('0.34 < feat3 <= 0.58', -0.018399675289672447)],
        'class2': [('feat0=0', 0.39540245003313673),
                   ('feat1=1', 0.0776798600683633),
                   ('0.07 < feat2 <= 0.22', 0.039268637636524654),
                   ('0.34 < feat3 <= 0.58', 0.025521020693166262)]}
    assert is_explain_equal(categorical_results,explained_categorical)

    structure_array = np.array([
        (0, 0, 0.08, 0.69),
        (1, 0, 0.03, 0.29),
        (0, 1, 0.99, 0.82),
        (2, 1, 0.73, 0.48),
        (1, 0, 0.36, 0.89),
        (0, 1, 0.07, 0.21)], dtype=[('a', 'i'), ('b', 'i'), ('c', 'f'),
                                    ('d', 'f')])
    lime = Lime(structure_array, PREDICTOR, class_names=CLASS_NAMES,
                feature_names=FEATURE_NAMES)
    explained_numerical_structure = lime.explain_instance(STRUCT_SAMPLE)
    assert is_explain_equal(explained_numerical_structure, numerical_results)
    lime = Lime(structure_array, PREDICTOR, class_names=CLASS_NAMES,
                feature_names=FEATURE_NAMES,
                categorical_indices=np.array(['a', 'b']))
    explained_categorical_structure = lime.explain_instance(STRUCT_SAMPLE)
    assert is_explain_equal(explained_categorical_structure, categorical_results)