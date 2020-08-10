# Sauder Automated Video Editor
Python script that automates post-processiing for educational video content at Sauder

_In development_

## TODO
* Summary
* Setup
    * with venv and pip
    * wich conda
* How to use, project structure, etc

## Important Information 
* Only supports **1920x1080**
* `/output` directory will be cleared at the start of each run (this behaviour will likely change)
* Body should be a single video clip with _approx. 3_ seconds before/after the spaeker speaks
* Watermark position defaults to bottom-right -> bottom left only if Watermark Position is **l** (in CSV)
* Only supports single line titles (titles can not exceed 45 characters)
