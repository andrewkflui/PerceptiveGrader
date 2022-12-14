import os
PROJECT_NAME = 'grading_system'
ROOT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
PROJECT_INITIAL_PATH = os.path.join(ROOT_PATH, '..', 'data', 'projects')
LOG_PATH = os.path.join(ROOT_PATH, 'data', 'log')

VERSION = 6

DISTANCE_FUNCTION = 'angular'
EPSILON = 1e-06

RD_CUTOFF = None
DEFAULT_RD_PERCENTILE_CUTOFF = 0.1
RD_CUTOFF_WINDOW_SIZE = None
RD_DERIVING_FACTOR = 0.5

DELTA_LINK_THRESHOLD = None
DELTA_LINK_THRESHOLD_FACTOR = None
DELTA_LINK_THRESHOLD_WINDOW_SIZE_FACTOR =  0.1

GRADE_ASSIGNMENT_METHOD = 'parent_breaks' # parent / parent_breaks / nearest_true_grade / gaussian_mixture / oc / moc
VOTING_VERSION = 'weighted_average'	# average / weightwd_average / lowest / majority

###  Version < 6 parameters
RELEVANT_SUBSPACE_NUMBER = 0
SUBSPACE_REPLACEMENT_RATIO = None
RESET_EXCLUSION_RD_FACTOR = True

EXCLUSION_RD_FACTOR = 4.
MIN_EXCLUSION_RD_FACTOR = 0.
EXCLUSION_RD_DEDUCTION_FACTOR = 0.25

MARGINALNESS_NEIGHBOURHOOD_SIZE = None
MARGINALNESS_RD_FACTOR = 1.
SPACIOUSNESS_NEIGHBOUR_NUMBER = 5

OUTLIER_REMOVAL = False
OUTLIER_DENSITY_CONDITION = '== 0'
OUTLIER_SPACIOUSNESS_CONDITION = '>= 0'
OUTLIER_NEAREST_TRUE_GRADE_CONDITION = '> RD * 3'

LABEL_SEARCHING_BOUNDARY_FACTOR = 2.0
LABEL_KNN = 5
### End of version < 6 parameters

DEBUG = False

# RANDOM_SEED = 3
RANDOM_SEED = 0
# RANDOM_SEED = None