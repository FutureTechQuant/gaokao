python -m pip install --upgrade pip
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
}
python -m crawler.pipeline.discover
python -m crawler.pipeline.collect
