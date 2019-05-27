#!/usr/bin/env python3
# -*- coding: utf8 -*-

# Copyright 2018-2019 Daisuke Sato
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import csv
import threading
import tkinter as tk
from tkinter import filedialog as tkFileDialog
from tkinter.scrolledtext import ScrolledText
from google.cloud import automl_v1beta1

VERSION = "0.0.2"


class ZFImageRFrame(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()
        self.key_file = ()
        self.target_files = ()

    def create_widgets(self):
        self.lbl_titile = tk.Label(self, text="ZF-ImageR v{}".format(VERSION), width=20, font=("",20))
        self.lbl_titile.pack()
        """
        project setting UI
        """
        frame_project_setting = tk.Frame(self)
        frame_project_setting.pack()

        # project id
        lbl_projectid = tk.Label(frame_project_setting, text="Project ID: ", width=20)
        lbl_projectid.grid(row=0, column=0)
        self.txt_projectid = tk.Entry(frame_project_setting, justify="left", width=35)
        self.txt_projectid.grid(row=0, column=1, sticky="w")
        self.txt_projectid.insert(tk.END, "rapid-domain-223007")

        # model id
        lbl_modelid = tk.Label(frame_project_setting, text="Model ID: ", width=20)
        lbl_modelid.grid(row=1, column=0)
        self.txt_modelid = tk.Entry(frame_project_setting, justify="left", width=35)
        self.txt_modelid.grid(row=1, column=1, sticky="w")
        self.txt_modelid.insert(tk.END, "ICN3656487066512753326")

        # gcp key
        lbl_keyfile = tk.Label(frame_project_setting, text="GCP Key File: ", width=20)
        lbl_keyfile.grid(row=2, column=0)
        frame_gcp_key_file_selection = tk.Frame(frame_project_setting, bg="white")
        frame_gcp_key_file_selection.grid(row=2, column=1, sticky="w", pady=(0, 5))
        self.txt_keyfile = tk.Entry(frame_gcp_key_file_selection, width=35)
        self.txt_keyfile.pack(side=tk.LEFT)
        self.txt_keyfile.insert(tk.END, "No Key File Selected")
        self.txt_keyfile.configure(state="disabled")
        btn_key_select = tk.Button(frame_gcp_key_file_selection, text="Select", command=self.load_key_file)
        btn_key_select.pack(side=tk.LEFT)

        """
        save dir select UI
        """
        lbl_savedir = tk.Label(frame_project_setting, text="Result Output Directory: ", width=20)
        lbl_savedir.grid(row=3, column=0)
        frame_save_dir_selection = tk.Frame(frame_project_setting, bg="white")
        frame_save_dir_selection.grid(row=3, column=1, sticky="w", pady=(0, 5))
        self.txt_savedir = tk.Entry(frame_save_dir_selection, width=35)
        self.txt_savedir.pack(side=tk.LEFT)
        self.txt_savedir.insert(tk.END, "No Directory Selected")
        self.txt_savedir.configure(state="disabled")
        btn_savedir_select = tk.Button(frame_save_dir_selection, text="Select", command=self.select_save_dir)
        btn_savedir_select.pack(side=tk.LEFT)

        """
        file select, process UI
        """
        frame_file_setting = tk.Frame(self)
        frame_file_setting.pack()

        lbl_filelist = tk.Label(frame_file_setting, text="Selected Image File(s):", width=20)
        # lbl_filelist.grid(row=4, column=0)
        lbl_filelist.pack()
        self.txt_filelist = ScrolledText(frame_file_setting, width=100, height=10)
        self.txt_filelist.pack(padx=3, pady=3, fill="both", expand=1)
        self.txt_filelist.insert(tk.INSERT, "No Files Selected")

        frame_file_process = tk.Frame(frame_file_setting)
        frame_file_process.pack()
        btn_img_select = tk.Button(frame_file_process, text="Select Image File(s)", command=self.load_files)
        btn_img_select.pack(side=tk.LEFT)
        self.btn_img_process = tk.Button(frame_file_process, text="Process File(s)", command=self.process_files)
        self.btn_img_process.pack(side=tk.LEFT)

        """
        progress bar
        """

        self.process_status = tk.Label(root, text="Ready.", borderwidth=2, relief="groove")
        self.process_status.pack(side=tk.BOTTOM, fill=tk.X)

    def showinfo(self):
        msg = "ZF-ImageR Ver."+VERSION+"\n\nGitHub: https://github.com/YShimada0419/ZF-ImageR"
        tk.messagebox.showinfo("About", msg)

    def load_key_file(self):
        self.key_file = tkFileDialog.askopenfilenames(parent=root, title='Choose a key file')
        file_list = ""
        for f in self.key_file:
            if not len(file_list) == 0:
                file_list += "\n"
            file_list += f
        self.txt_keyfile.configure(state="normal")
        self.txt_keyfile.delete(0, tk.END)
        self.txt_keyfile.insert(tk.INSERT, file_list)
        self.process_status["text"] = "key file selected."

    def load_files(self):
        self.target_files = tkFileDialog.askopenfilenames(parent=root, title='Choose image files')
        file_list = ""
        for f in self.target_files:
            if not len(file_list) == 0:
                file_list += "\n"
            file_list += f
        self.txt_filelist.delete(1.0, tk.END)
        self.txt_filelist.insert(tk.INSERT, file_list)
        self.process_status["text"] = "{} file selected.".format(str(len(self.target_files))) \
            if len(self.target_files) == 1 else "{} files selected.".format(str(len(self.target_files)))

    def select_save_dir(self):
        self.save_dir = tkFileDialog.askdirectory(parent=root, title='Choose save dir.')
        self.txt_savedir.configure(state="normal")
        self.txt_savedir.delete(0, tk.END)
        self.txt_savedir.insert(tk.INSERT, self.save_dir)

    def process_files(self):
        files = self.target_files
        key = self.key_file[0]
        self.process_status["text"] = "Processing {} images".format(len(files))
        self.btn_img_process.configure(state=tk.DISABLED)
        # process_image(args=files, project_id=self.txt_projectid.get(), model_id=self.txt_modelid.get(),
        #               key_file=key, save_dir=self.save_dir, gui=self)
        p = threading.Thread(target=process_image, args=(files, self.txt_projectid.get(), self.txt_modelid.get(),
                      key, self.save_dir, self))
        p.start()


class GCP(object):
    def __init__(self, project_id=None, model_id=None, app_credentials=None):
        if project_id is not None:
            self.set_project_id(project_id)
        if model_id is not None:
            self.set_model_id(model_id)
        if app_credentials is not None:
            self.set_app_credentials(app_credentials)

    def set_project_id(self, project_id):
        self.project_id = project_id

    def set_model_id(self, model_id):
        self.model_id = model_id

    def set_app_credentials(self, path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path

    def get_predict_result(self, content):
        prediction_client = automl_v1beta1.PredictionServiceClient()
        name = 'projects/{}/locations/us-central1/models/{}'.format(self.project_id, self.model_id)
        payload = {'image': {'image_bytes': content}}
        params = {}
        request = prediction_client.predict(name, payload, params)
        return request  # waits till request is returned

    def get_prediction(self, content):
        result = self.get_predict_result(content)
        return result.payload[0].classification.score, result.payload[0].display_name


def process_image(args, project_id, model_id, key_file, save_dir, gui):
    files = len(args)
    gcp = GCP()
    gcp.set_project_id(project_id)
    gcp.set_model_id(model_id)
    gcp.set_app_credentials(key_file)
    print("key:", key_file)
    print("gcp:", gcp.project_id, gcp.model_id)
    results = []
    for i in range(0, files):
        file_path = args[i]
        gui.process_status["text"] = "Processing {}/{}".format(i+1, files)
        with open(file_path, 'rb') as ff:
            content = ff.read()
        result = list((file_path,) + gcp.get_prediction(content))
        print(result)
        results.append(result)
    with open(save_dir + "/results.csv", "a") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerows(results)
    gui.btn_img_process.configure(state=tk.NORMAL)
    gui.process_status["text"] = "Finished processing. Results saved to {}/results.csv.".format(save_dir)


if __name__ == '__main__':
    root = tk.Tk()
    root.title("ZF-ImageR")
    root.geometry('600x400')
    menubar = tk.Menu(root)

    app = ZFImageRFrame(master=root)

    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Open", command=app.load_files)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="About", command=app.showinfo)
    menubar.add_cascade(label="Help", menu=helpmenu)
    root.config(menu=menubar)

    """
    main
    """
    root.mainloop()
