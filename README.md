# Perceptive Grader

A web-based demonstration system of short answer grading based on interactive model building with active learning

Copyright (C) 2021 - Andrew Kwok-Fai Lui, Vanessa Sin-Chun Ng, Stella Cheung Wing-Nga

The Open University of Hong Kong

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not, see http://www.gnu.org/licenses/.

## Introduction

The Short Answer Grading with Active Learning (SAGAL) algorithm aims to optimize the grading examples for training short answer grading models. The underlying active learning approach works in an interactive fashion that involves a cycle of selecting data for annotation and updating the model. PerceptiveGrader is 
a web-based demonstration system of short answer grading based on SAGAL. Please refer to the following paper for the details.

> Lui, A.K.F., Ng, S.C. and Cheung, S.W.N., 2022. An Interactive Short Answer Grading System based on Active Learning Models, presented at the 4th International Confernece on Computer Science and Technologies in Education, 6-8 May, 2022.

The details of SAGAL can be found in the following paper.

> Lui, A.K., Ng, S.C. and S.W.N. Cheung (in press), Automated Short Answer Grading with Computer-Assisted Grading Example Acquisition based on Active Learning, Interactive Learning Environment

#### Related Software

* [SAGAL](https://github.com/andrewkflui/SAGAL): A prototype implementation of the Short Answer Grading with Active Learning (SAGAL) algorithm and the programs for the experiments described in the paper.

### Prerequisites

#### Python 3.7.3 (For Non M1 Chip Devices)
This project relies on Python 3.7.3. Please download and install it from https://www.python.org/downloads/release/python-373/

#### Conda (For Devices with M1 Chip)
Please download and install Conda
https://docs.conda.io/projects/conda/en/latest/user-guide/install/macos.html

#### Installation of Pre-trained models
The project requires the following pre-trained models for text encoding. Please download and put them under *data/models/pretrained/{ENCODER_NAME}/* inside the project folder.

##### Google Universal Sentence Encoder

`{ENCODER_NAME} = google_universal_sentence_encoder`

https://tfhub.dev/google/universal-sentence-encoder/4

##### GloVe

`{ENCODER_NAME} = glove`

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

### Screen Shots

The following shows the screen shots of the running of the browser-based PerceptiveGrader

<img width="696" alt="Screenshot 2022-10-30 at 2 03 57 PM" src="https://user-images.githubusercontent.com/8808539/198864966-61442f1c-bdcf-479f-8d93-775288abd693.png">
The main client panel of PerceptiveGrader. The project screen displays the key characteristics of the question-and-answer set. The speciousness ranked data distribution is shown on the right, from which the default values of MASD and ADT are shown. The bottom shows a 2D projection of the data distribution.

<img width="692" alt="Screenshot 2022-10-30 at 2 04 10 PM" src="https://user-images.githubusercontent.com/8808539/198864978-5dd61c37-d027-4444-8a52-8c504b83e7c2.png">
The annotation panel (left) where the top ranked answers may be assessed and graded.  Clicking on an answer row would bring up the answer panel (right) that details neighborhood of the answer.

## Acknowledgement
The work described in this paper was fully supported by a grant from the Research Grants Council of the Hong Kong Special Administrative Region, China (UGC/FDS16/E10/19).


