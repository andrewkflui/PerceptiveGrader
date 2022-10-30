# GAL Grading System

### Prerequisites

#### Python 3.7.3 (For Non M1 Chip Devices)
This project relies on Python 3.7.3. Please download and install it from https://www.python.org/downloads/release/python-373/

#### Conda (For Devices with M1 Chip)
Please download and install Conda
https://docs.conda.io/projects/conda/en/latest/user-guide/install/macos.html

#### Pre-trained models
The project requires the following pre-trained models for text encoding. Please download and put them under *data/models/pretrained/{ENCODER_NAME}/* inside the project folder.

##### Google Universal Sentence Encoder

{ENCODER_NAME} = google_universal_sentence_encoder

https://tfhub.dev/google/universal-sentence-encoder/4

##### GloVe

{ENCODER_NAME} = glove

https://nlp.stanford.edu/projects/glove/

### Running With Virutal Environment (For Non M1 Chip Devices)

1. Create a virtual environment that runs with Python 3.7.3
2. Activate it and run
   * MacOS <br/>
   > pip install -r requirements_tf2.txt --no-deps
   * Windows <br/>
   > pip install -r requirements_windows.txt --no-deps
<!-- Please run the following line(s) after the above installation:
   > python -m spacy download en_core_web_sm -->
3. Open Terminal / CMD, go to the project root and run:
   > python web/executor.py

### Running With Conda Environment

1. Create a conda environment that runs with Python 3.9.4
2. Install the denpendencies according to VE_M1.yml
3. Open Terminal / CMD, go to the project root and run:
   > python web/executor.py

### Running from script

* MacOS
  Double click ***execute_script.sh.command*** to run

* Windows
  1. Download Git from https://git-scm.com/downloads
  2. Install Git. Remember to check "**Associate .sh file to be run with Bash**".
  3. Double click ***execute_script.sh*** to run

The API and client server shall be started and Chrome browser would be opened automatically.

### Input Dataset

The input dataset should be a csv file of the following format
[Question ID, Question Text, Answer ID, Answer Text, Is Reference]

Some csv files are provided under data/datasets/raw/seb2custom as examples
