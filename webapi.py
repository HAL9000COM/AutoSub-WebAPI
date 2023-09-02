# -*- coding: utf-8 -*-

from flask import Flask, request, send_file
import os
import json
import subprocess
import cherrypy
import argparse
import logging

app = Flask(__name__)

upload_folder = "uploads"
os.makedirs(upload_folder, exist_ok=True)

model = "models/deepspeech-0.9.3-models.pbmm"
scorer = "models/deepspeech-0.9.3-models.scorer"
engine = "ds"


@app.route("/transcribe", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "Missing file", 400
    up_file = request.files["file"]

    settings = {}
    for key in request.form.keys():
        settings[key] = request.form[key]

    # save the file
    filename = up_file.filename
    file_path = os.path.join(upload_folder, filename)
    up_file.save(file_path)
    logging.info(f"Saved file to {file_path}")

    out_format = settings.get("format", "srt")
    split_duration = settings.get("split-duration", 5)
    file_path = os.path.abspath(file_path).replace("\\", "/")
    logging.info(
        f"Transcribing {file_path} to format {out_format} and split duration {split_duration}"
    )
    logging.info(f"Using engine {engine}, model {model} and scorer {scorer}")
    autosub_process = subprocess.run(
        [
            "python",
            "autosub/main.py",
            "--file",
            str(file_path),
            "--format",
            out_format,
            "--split-duration",
            str(split_duration),
            "--engine",
            engine,
            "--model",
            os.path.abspath(model).replace("\\", "/"),
            "--scorer",
            os.path.abspath(scorer).replace("\\", "/"),
        ],
        text=True,  # Capture output as text (Python 3.5+)
        stdout=subprocess.PIPE,  # Capture stdout
        stderr=subprocess.PIPE,  # Capture stderr
    )
    exit_code = autosub_process.returncode
    # Access the captured output
    stdout_output = autosub_process.stdout
    stderr_output = autosub_process.stderr
    if exit_code != 0:
        logging.error(f"Error running autosub: {stderr_output}")
        return stderr_output, 500
    # wait for the process to finish
    # return the file
    video_prefix = os.path.splitext(os.path.basename(file_path))[0]
    out_path = os.path.join("output", video_prefix + "." + out_format)
    logging.info(f"Returning file {out_path}")
    return send_file(out_path), 200


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--engine", help="select the engine to use. options: 'ds', 'stt'", default="ds"
    )
    parser.add_argument(
        "--model",
        help="select the model to use",
        default="models/deepspeech-0.9.3-models.pbmm",
    )
    parser.add_argument(
        "--scorer",
        help="select the scorer to use",
        default="models/deepspeech-0.9.3-models.scorer",
    )
    parser.add_argument("--port", help="select the port to use", default=5000)
    parser.add_argument(
        "--max-size", help="select the max size to use", default=1024 * 1024 * 1024
    )
    args = parser.parse_args()
    if args.engine:
        engine = str(args.engine)
    if args.model:
        model = str(args.model)
    if args.scorer:
        scorer = str(args.scorer)
    if args.port:
        port = int(args.port)
    if args.max_size:
        max_size = int(args.max_size)
    cherrypy.tree.graft(app, "/")
    cherrypy.config.update(
        {
            "server.socket_host": "0.0.0.0",
            "server.socket_port": port,
            "engine.autoreload.on": True,
            "server.max_request_body_size": max_size,
        }
    )
    logging.info(
        f"Starting server on port {port}, engine {engine}, model {model} and scorer {scorer}, max size {max_size}"
    )
    cherrypy.engine.start()
    cherrypy.engine.block()
