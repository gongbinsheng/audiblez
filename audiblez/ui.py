#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# A simple wxWidgets UI for audiblez

import torch.cuda
import torch.backends.mps
import numpy as np
import soundfile
import threading
import platform
import subprocess
import io
import os
import wx
from wx.lib.newevent import NewEvent
from wx.lib.scrolledpanel import ScrolledPanel
from PIL import Image
from tempfile import NamedTemporaryFile
from pathlib import Path

from audiblez.voices import voices, flags
from audiblez.settings import get_settings

EVENTS = {
    'CORE_STARTED': NewEvent(),
    'CORE_PROGRESS': NewEvent(),
    'CORE_CHAPTER_STARTED': NewEvent(),
    'CORE_CHAPTER_FINISHED': NewEvent(),
    'CORE_FINISHED': NewEvent()
}

border = 5


class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        # Load settings
        self.settings = get_settings()

        # Use saved window size or calculate default
        saved_width, saved_height = self.settings.get_window_size()
        screen_width, screen_h = wx.GetDisplaySize()

        # Use saved size if reasonable, otherwise use default calculation
        if saved_width < 400 or saved_width > screen_width:
            saved_width = int(screen_width * 0.6)
        if saved_height < 300 or saved_height > screen_h:
            saved_height = saved_width * 3 // 4

        self.window_width = saved_width
        super().__init__(parent, title=title, size=(saved_width, saved_height))

        self.chapters_panel = None
        self.preview_threads = []
        self.selected_chapter = None
        self.selected_book = None
        self.synthesis_in_progress = False

        # Bind close event to save settings
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.Bind(EVENTS['CORE_STARTED'][1], self.on_core_started)
        self.Bind(EVENTS['CORE_CHAPTER_STARTED'][1], self.on_core_chapter_started)
        self.Bind(EVENTS['CORE_CHAPTER_FINISHED'][1], self.on_core_chapter_finished)
        self.Bind(EVENTS['CORE_PROGRESS'][1], self.on_core_progress)
        self.Bind(EVENTS['CORE_FINISHED'][1], self.on_core_finished)

        self.create_menu()
        self.create_layout()
        self.Centre()
        self.Show(True)
        if Path('../epub/lewis.epub').exists(): self.open_epub('../epub/lewis.epub')

    def create_menu(self):
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        open_item = wx.MenuItem(file_menu, wx.ID_OPEN, "&Open\tCtrl+O")
        file_menu.Append(open_item)
        self.Bind(wx.EVT_MENU, self.on_open, open_item)  # Bind the event

        exit_item = wx.MenuItem(file_menu, wx.ID_EXIT, "&Exit\tCtrl+Q")
        file_menu.Append(exit_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)

        menubar.Append(file_menu, "&File")
        self.SetMenuBar(menubar)

    def on_core_started(self, event):
        print('CORE_STARTED')
        self.progress_bar_label.Show()
        self.progress_bar.Show()
        self.progress_bar.SetValue(0)
        self.progress_bar.Layout()
        self.eta_label.Show()
        self.params_panel.Layout()
        self.synth_panel.Layout()

    def on_core_chapter_started(self, event):
        # print('CORE_CHAPTER_STARTED', event.chapter_index)
        self.set_table_chapter_status(event.chapter_index, "⏳ In Progress")

    def on_core_chapter_finished(self, event):
        # print('CORE_CHAPTER_FINISHED', event.chapter_index)
        self.set_table_chapter_status(event.chapter_index, "✅ Done")
        self.start_button.Show()

    def on_core_progress(self, event):
        # print('CORE_PROGRESS', event.progress)
        self.progress_bar.SetValue(event.stats.progress)
        self.progress_bar_label.SetLabel(f"Synthesis Progress: {event.stats.progress}%")
        self.eta_label.SetLabel(f"Estimated Time Remaining: {event.stats.eta}")
        self.synth_panel.Layout()

    def on_core_finished(self, event):
        self.synthesis_in_progress = False
        self.open_folder_with_explorer(self.output_folder_text_ctrl.GetValue())

    def create_layout(self):
        # Panels layout looks like this:
        # splitter
        #     splitter_left
        #         chapters_panel
        #     splitter_right
        #         center_panel
        #             text_area
        #         right_panel
        #             book_info_panel_box
        #                 book_info_panel
        #                     cover_bitmap
        #                     book_details_panel
        #             param_panel_box
        #                  param_panel
        #                      ...
        #             synth_panel_box
        #                  synth_panel
        #                      start_button
        #                      ...

        top_panel = wx.Panel(self)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_panel.SetSizer(top_sizer)

        # Open Epub button
        open_epub_button = wx.Button(top_panel, label="📁 Open EPUB")
        open_epub_button.Bind(wx.EVT_BUTTON, self.on_open)
        top_sizer.Add(open_epub_button, 0, wx.ALL, 5)

        # Open Markdown .md
        # open_md_button = wx.Button(top_panel, label="📁 Open Markdown (.md)")
        # open_md_button.Bind(wx.EVT_BUTTON, self.on_open)
        # top_sizer.Add(open_md_button, 0, wx.ALL, 5)

        # Open .txt
        # open_txt_button = wx.Button(top_panel, label="📁 Open .txt")
        # open_txt_button.Bind(wx.EVT_BUTTON, self.on_open)
        # top_sizer.Add(open_txt_button, 0, wx.ALL, 5)

        # Open PDF
        # open_pdf_button = wx.Button(top_panel, label="📁 Open PDF")
        # open_pdf_button.Bind(wx.EVT_BUTTON, self.on_open)
        # top_sizer.Add(open_pdf_button, 0, wx.ALL, 5)

        # About button
        help_button = wx.Button(top_panel, label="ℹ️ About")
        help_button.Bind(wx.EVT_BUTTON, lambda event: self.about_dialog())
        top_sizer.Add(help_button, 0, wx.ALL, 5)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.main_sizer)

        # self.splitter = wx.SplitterWindow(self, -1)
        # self.splitter.SetSashGravity(0.9)
        self.splitter = wx.Panel(self)
        self.splitter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.splitter.SetSizer(self.splitter_sizer)

        self.main_sizer.Add(top_panel, 0, wx.ALL | wx.EXPAND, 5)
        self.main_sizer.Add(self.splitter, 1, wx.EXPAND)

    def create_layout_for_ebook(self, splitter):
        splitter_left = wx.Panel(splitter, -1)
        splitter_right = wx.Panel(self.splitter)
        self.splitter_left, self.splitter_right = splitter_left, splitter_right
        self.splitter_sizer.Add(splitter_left, 1, wx.ALL | wx.EXPAND, 5)
        self.splitter_sizer.Add(splitter_right, 2, wx.ALL | wx.EXPAND, 5)

        self.left_sizer = wx.BoxSizer(wx.VERTICAL)
        splitter_left.SetSizer(self.left_sizer)

        # add center panel with large text area
        self.center_panel = wx.Panel(splitter_right)
        self.center_sizer = wx.BoxSizer(wx.VERTICAL)
        self.center_panel.SetSizer(self.center_sizer)
        self.text_area = wx.TextCtrl(self.center_panel, style=wx.TE_MULTILINE, size=(int(self.window_width * 0.4), -1))
        font = wx.Font(14, wx.MODERN, wx.NORMAL, wx.NORMAL)
        self.text_area.SetFont(font)
        # On text change, update the extracted_text attribute of the selected_chapter:
        self.text_area.Bind(wx.EVT_TEXT, lambda event: setattr(self.selected_chapter, 'extracted_text', self.text_area.GetValue()))

        self.chapter_label = wx.StaticText(
            self.center_panel, label=f'Edit / Preview content for section "{self.selected_chapter.short_name}":')
        preview_button = wx.Button(self.center_panel, label="🔊 Preview")
        preview_button.Bind(wx.EVT_BUTTON, self.on_preview_chapter)

        self.center_sizer.Add(self.chapter_label, 0, wx.ALL, 5)
        self.center_sizer.Add(preview_button, 0, wx.ALL, 5)
        self.center_sizer.Add(self.text_area, 1, wx.ALL | wx.EXPAND, 5)

        splitter_right_sizer = wx.BoxSizer(wx.HORIZONTAL)
        splitter_right.SetSizer(splitter_right_sizer)

        self.create_right_panel(splitter_right)
        splitter_right_sizer.Add(self.center_panel, 1, wx.ALL | wx.EXPAND, 5)
        splitter_right_sizer.Add(self.right_panel, 1, wx.ALL | wx.EXPAND, 5)

    def about_dialog(self):
        msg = ("A simple tool to generate audiobooks from EPUB files using Kokoro-82M models\n" +
               "Distributed under the MIT License.\n\n" +
               "by Claudio Santini 2025\nand many contributors.\n\n" +
               "https://claudio.uk\n\n")
        wx.MessageBox(msg, "Audiblez")

    def create_right_panel(self, splitter_right):
        self.right_panel = wx.Panel(splitter_right)
        self.right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.right_panel.SetSizer(self.right_sizer)

        self.book_info_panel_box = wx.Panel(self.right_panel, style=wx.SUNKEN_BORDER)
        book_info_panel_box_sizer = wx.StaticBoxSizer(wx.VERTICAL, self.book_info_panel_box, "Book Details")
        self.book_info_panel_box.SetSizer(book_info_panel_box_sizer)
        self.right_sizer.Add(self.book_info_panel_box, 1, wx.ALL | wx.EXPAND, 5)

        self.book_info_panel = wx.Panel(self.book_info_panel_box, style=wx.BORDER_NONE)
        self.book_info_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.book_info_panel.SetSizer(self.book_info_sizer)
        book_info_panel_box_sizer.Add(self.book_info_panel, 1, wx.ALL | wx.EXPAND, 5)

        # Add cover image
        self.cover_bitmap = wx.StaticBitmap(self.book_info_panel, -1)
        self.book_info_sizer.Add(self.cover_bitmap, 0, wx.ALL, 5)

        self.cover_bitmap.Refresh()
        self.book_info_panel.Refresh()
        self.book_info_panel.Layout()
        self.cover_bitmap.Layout()

        self.create_book_details_panel()
        self.create_params_panel()
        self.create_synthesis_panel()

    def create_book_details_panel(self):
        book_details_panel = wx.Panel(self.book_info_panel)
        book_details_sizer = wx.GridBagSizer(10, 10)
        book_details_panel.SetSizer(book_details_sizer)
        self.book_info_sizer.Add(book_details_panel, 1, wx.ALL | wx.EXPAND, 5)

        # Add title
        title_label = wx.StaticText(book_details_panel, label="Title:")
        title_text = wx.StaticText(book_details_panel, label=self.selected_book_title)
        book_details_sizer.Add(title_label, pos=(0, 0), flag=wx.ALL, border=5)
        book_details_sizer.Add(title_text, pos=(0, 1), flag=wx.ALL, border=5)

        # Add Author
        author_label = wx.StaticText(book_details_panel, label="Author:")
        author_text = wx.StaticText(book_details_panel, label=self.selected_book_author)
        book_details_sizer.Add(author_label, pos=(1, 0), flag=wx.ALL, border=5)
        book_details_sizer.Add(author_text, pos=(1, 1), flag=wx.ALL, border=5)

        # Add Total length
        length_label = wx.StaticText(book_details_panel, label="Total Length:")
        if not hasattr(self, 'document_chapters'):
            total_len = 0
        else:
            total_len = sum([len(c.extracted_text) for c in self.document_chapters])
        length_text = wx.StaticText(book_details_panel, label=f'{total_len:,} characters')
        book_details_sizer.Add(length_label, pos=(2, 0), flag=wx.ALL, border=5)
        book_details_sizer.Add(length_text, pos=(2, 1), flag=wx.ALL, border=5)

    def create_params_panel(self):
        panel_box = wx.Panel(self.right_panel, style=wx.SUNKEN_BORDER)
        panel_box_sizer = wx.StaticBoxSizer(wx.VERTICAL, panel_box, "Audiobook Parameters")
        panel_box.SetSizer(panel_box_sizer)

        panel = self.params_panel = wx.Panel(panel_box)
        panel_box_sizer.Add(panel, 1, wx.ALL | wx.EXPAND, 5)
        self.right_sizer.Add(panel_box, 1, wx.ALL | wx.EXPAND, 5)
        sizer = wx.GridBagSizer(10, 10)
        panel.SetSizer(sizer)

        engine_label = wx.StaticText(panel, label="Engine:")
        engine_radio_panel = wx.Panel(panel)
        self.cpu_radio = wx.RadioButton(engine_radio_panel, label="CPU", style=wx.RB_GROUP)
        self.cuda_radio = wx.RadioButton(engine_radio_panel, label="CUDA")
        self.apple_radio = wx.RadioButton(engine_radio_panel, label="Apple Silicon")

        # Check which engines are available and disable unavailable ones
        available_engines = self.settings.get_available_engines()

        # Disable unavailable engines and set tooltips
        if not available_engines['cuda']:
            self.cuda_radio.Enable(False)
            self.cuda_radio.SetToolTip("CUDA is not available on this system")
        else:
            self.cuda_radio.SetToolTip("Use NVIDIA GPU acceleration")

        if not available_engines['apple']:
            self.apple_radio.Enable(False)
            self.apple_radio.SetToolTip("Apple Silicon (MPS) is not available on this system")
        else:
            self.apple_radio.SetToolTip("Use Apple Silicon GPU acceleration")

        # CPU is always available
        self.cpu_radio.SetToolTip("Use CPU for processing (always available)")

        # Set engine based on saved settings (already validated by settings module)
        saved_engine = self.settings.get_engine()
        if saved_engine == 'apple':
            self.apple_radio.SetValue(True)
            torch.set_default_device('mps')
        elif saved_engine == 'cuda':
            self.cuda_radio.SetValue(True)
            torch.set_default_device('cuda')
        else:
            self.cpu_radio.SetValue(True)
            torch.set_default_device('cpu')

        sizer.Add(engine_label, pos=(0, 0), flag=wx.ALL, border=border)
        sizer.Add(engine_radio_panel, pos=(0, 1), flag=wx.ALL, border=border)
        engine_radio_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        engine_radio_panel.SetSizer(engine_radio_panel_sizer)
        engine_radio_panel_sizer.Add(self.cpu_radio, 0, wx.ALL, 5)
        engine_radio_panel_sizer.Add(self.cuda_radio, 0, wx.ALL, 5)
        engine_radio_panel_sizer.Add(self.apple_radio, 0, wx.ALL, 5)
        self.cpu_radio.Bind(wx.EVT_RADIOBUTTON, lambda event: self._on_engine_changed('cpu'))
        self.cuda_radio.Bind(wx.EVT_RADIOBUTTON, lambda event: self._on_engine_changed('cuda'))
        self.apple_radio.Bind(wx.EVT_RADIOBUTTON, lambda event: self._on_engine_changed('apple'))

        # Create a list of voices with flags
        flag_and_voice_list = []
        for code, l in voices.items():
            for v in l:
                flag_and_voice_list.append(f'{flags[code]} {v}')

        voice_label = wx.StaticText(panel, label="Voice:")
        # Use saved voice or default to first voice
        saved_voice = self.settings.get_voice()
        if saved_voice and saved_voice in flag_and_voice_list:
            default_voice = saved_voice
        else:
            default_voice = flag_and_voice_list[0]
        self.selected_voice = default_voice
        self.voice_dropdown = wx.ComboBox(panel, choices=flag_and_voice_list, value=default_voice)
        self.voice_dropdown.Bind(wx.EVT_COMBOBOX, self.on_select_voice)
        sizer.Add(voice_label, pos=(1, 0), flag=wx.ALL, border=border)
        sizer.Add(self.voice_dropdown, pos=(1, 1), flag=wx.ALL, border=border)

        # Add dropdown for speed
        speed_label = wx.StaticText(panel, label="Speed:")
        saved_speed = str(self.settings.get_speed())
        self.speed_text_input = wx.TextCtrl(panel, value=saved_speed)
        self.selected_speed = saved_speed
        self.speed_text_input.Bind(wx.EVT_TEXT, self.on_select_speed)
        sizer.Add(speed_label, pos=(2, 0), flag=wx.ALL, border=border)
        sizer.Add(self.speed_text_input, pos=(2, 1), flag=wx.ALL, border=border)

        # Add file dialog selector to select output folder
        output_folder_label = wx.StaticText(panel, label="Output Folder:")
        saved_output_folder = self.settings.get_output_folder()
        self.output_folder_text_ctrl = wx.TextCtrl(panel, value=saved_output_folder)
        self.output_folder_text_ctrl.SetEditable(False)
        # self.output_folder_text_ctrl.SetMinSize((200, -1))
        output_folder_button = wx.Button(panel, label="📂 Select")
        output_folder_button.Bind(wx.EVT_BUTTON, self.open_output_folder_dialog)
        sizer.Add(output_folder_label, pos=(3, 0), flag=wx.ALL, border=border)
        sizer.Add(self.output_folder_text_ctrl, pos=(3, 1), flag=wx.ALL | wx.EXPAND, border=border)
        sizer.Add(output_folder_button, pos=(4, 1), flag=wx.ALL, border=border)

    def create_synthesis_panel(self):
        # Think and identify layout issue with the folling code
        panel_box = wx.Panel(self.right_panel, style=wx.SUNKEN_BORDER)
        panel_box_sizer = wx.StaticBoxSizer(wx.VERTICAL, panel_box, "Audiobook Generation Status")
        panel_box.SetSizer(panel_box_sizer)

        panel = self.synth_panel = wx.Panel(panel_box)
        panel_box_sizer.Add(panel, 1, wx.ALL | wx.EXPAND, 5)
        self.right_sizer.Add(panel_box, 1, wx.ALL | wx.EXPAND, 5)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)

        # Add Start button
        self.start_button = wx.Button(panel, label="🚀 Start Audiobook Synthesis")
        self.start_button.Bind(wx.EVT_BUTTON, self.on_start)
        sizer.Add(self.start_button, 0, wx.ALL, 5)

        # Add Stop button
        # self.stop_button = wx.Button(panel, label="⏹️ Stop Synthesis")
        # self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop)
        # sizer.Add(self.stop_button, 0, wx.ALL, 5)
        # self.stop_button.Hide()

        # Add Progress Bar label:
        self.progress_bar_label = wx.StaticText(panel, label="Synthesis Progress:")
        sizer.Add(self.progress_bar_label, 0, wx.ALL, 5)
        self.progress_bar = wx.Gauge(panel, range=100, style=wx.GA_PROGRESS)
        self.progress_bar.SetMinSize((-1, 30))
        sizer.Add(self.progress_bar, 0, wx.ALL | wx.EXPAND, 5)
        self.progress_bar_label.Hide()
        self.progress_bar.Hide()

        # Add ETA Label
        self.eta_label = wx.StaticText(panel, label="Estimated Time Remaining: ")
        self.eta_label.Hide()
        sizer.Add(self.eta_label, 0, wx.ALL, 5)

    def open_output_folder_dialog(self, event):
        with wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            output_folder = dialog.GetPath()
            print(f"Selected output folder: {output_folder}")
            self.output_folder_text_ctrl.SetValue(output_folder)

    def on_select_voice(self, event):
        self.selected_voice = event.GetString()

    def on_select_speed(self, event):
        speed = float(event.GetString())
        print('Selected speed', speed)
        self.selected_speed = speed

    def _on_engine_changed(self, engine):
        """Handle engine radio button changes"""
        if engine == 'cpu':
            torch.set_default_device('cpu')
        elif engine == 'cuda':
            torch.set_default_device('cuda')
        elif engine == 'apple':
            torch.set_default_device('mps')

    def _save_current_settings(self):
        """Save current UI settings to the settings file"""
        try:
            # Save window size
            size = self.GetSize()
            self.settings.set_window_size(size.width, size.height)

            # Save engine selection
            if self.cpu_radio.GetValue():
                self.settings.set_engine('cpu')
            elif self.cuda_radio.GetValue():
                self.settings.set_engine('cuda')
            elif self.apple_radio.GetValue():
                self.settings.set_engine('apple')

            # Save voice selection
            self.settings.set_voice(self.selected_voice)

            # Save speed
            self.settings.set_speed(float(self.selected_speed))

            # Save output folder
            self.settings.set_output_folder(self.output_folder_text_ctrl.GetValue())

            # Write to file
            self.settings.save_settings()

        except Exception as e:
            print(f"Warning: Failed to save settings: {e}")

    def on_close(self, event):
        """Handle window close event"""
        # Save settings before closing
        self._save_current_settings()

        # Close the window
        self.Destroy()

    def open_epub(self, file_path):
        # Cleanup previous layout
        if hasattr(self, 'selected_book'):
            self.splitter.DestroyChildren()

        self.selected_file_path = file_path
        print(f"Opening file: {file_path}")  # Do something with the filepath (e.g., parse the EPUB)

        from ebooklib import epub
        from audiblez.core import find_document_chapters_and_extract_texts, find_good_chapters, find_cover
        book = epub.read_epub(file_path)
        meta_title = book.get_metadata('DC', 'title')
        self.selected_book_title = meta_title[0][0] if meta_title else ''
        meta_creator = book.get_metadata('DC', 'creator')
        self.selected_book_author = meta_creator[0][0] if meta_creator else ''
        self.selected_book = book

        self.document_chapters = find_document_chapters_and_extract_texts(book)
        good_chapters = find_good_chapters(self.document_chapters)
        self.selected_chapter = good_chapters[0]
        for chapter in self.document_chapters:
            chapter.short_name = chapter.get_name().replace('.xhtml', '').replace('xhtml/', '').replace('.html', '').replace('Text/', '')
            chapter.is_selected = chapter in good_chapters

        self.create_layout_for_ebook(self.splitter)

        # Update Cover
        cover = find_cover(book)
        if cover is not None:
            pil_image = Image.open(io.BytesIO(cover.content))
            wx_img = wx.EmptyImage(pil_image.size[0], pil_image.size[1])
            wx_img.SetData(pil_image.convert("RGB").tobytes())
            cover_h = 200
            cover_w = int(cover_h * pil_image.size[0] / pil_image.size[1])
            wx_img.Rescale(cover_w, cover_h)
            self.cover_bitmap.SetBitmap(wx_img.ConvertToBitmap())
            self.cover_bitmap.SetMaxSize((200, cover_h))

        chapters_panel = self.create_chapters_table_panel(good_chapters)

        #  chapters_panel to left_sizer, or replace if it exists already
        if self.chapters_panel:
            self.left_sizer.Replace(self.chapters_panel, chapters_panel)
            self.chapters_panel.Destroy()
            self.chapters_panel = chapters_panel
        else:
            self.left_sizer.Add(chapters_panel, 1, wx.ALL | wx.EXPAND, 5)
            self.chapters_panel = chapters_panel

        # These two are very important:
        self.splitter_left.Layout()
        self.splitter_right.Layout()
        self.splitter.Layout()

    def on_table_checked(self, event):
        self.document_chapters[event.GetIndex()].is_selected = True

    def on_table_unchecked(self, event):
        self.document_chapters[event.GetIndex()].is_selected = False

    def on_table_selected(self, event):
        chapter = self.document_chapters[event.GetIndex()]
        print('Selected', event.GetIndex(), chapter.short_name)
        self.selected_chapter = chapter
        self.text_area.SetValue(chapter.extracted_text)
        self.chapter_label.SetLabel(f'Edit / Preview content for section "{chapter.short_name}":')

    def create_chapters_table_panel(self, good_chapters):
        panel = ScrolledPanel(self.splitter_left, -1, style=wx.TAB_TRAVERSAL | wx.SUNKEN_BORDER)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)

        self.table = table = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        table.InsertColumn(0, "Included")
        table.InsertColumn(1, "Chapter Name")
        table.InsertColumn(2, "Chapter Length")
        table.InsertColumn(3, "Status")
        table.SetColumnWidth(0, 80)
        table.SetColumnWidth(1, 150)
        table.SetColumnWidth(2, 150)
        table.SetColumnWidth(3, 100)
        table.SetSize((250, -1))
        table.EnableCheckBoxes()
        table.Bind(wx.EVT_LIST_ITEM_CHECKED, self.on_table_checked)
        table.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.on_table_unchecked)
        table.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_table_selected)

        for i, chapter in enumerate(self.document_chapters):
            auto_selected = chapter in good_chapters
            table.Append(['', chapter.short_name, f"{len(chapter.extracted_text):,}"])
            if auto_selected: table.CheckItem(i)

        title_text = wx.StaticText(panel, label=f"Select chapters to include in the audiobook:")
        sizer.Add(title_text, 0, wx.ALL, 5)
        sizer.Add(table, 1, wx.ALL | wx.EXPAND, 5)
        return panel

    def get_selected_voice(self):
        return self.selected_voice.split(' ')[1]

    def get_selected_speed(self):
        return float(self.selected_speed)

    def on_preview_chapter(self, event):
        lang_code = self.get_selected_voice()[0]
        button = event.GetEventObject()
        button.SetLabel("⏳")
        button.Disable()

        def generate_preview():
            import audiblez.core as core
            from kokoro import KPipeline
            pipeline = KPipeline(lang_code=lang_code)
            core.load_spacy()
            text = self.selected_chapter.extracted_text[:300]
            if len(text) == 0: return
            audio_segments = core.gen_audio_segments(
                pipeline,
                text,
                voice=self.get_selected_voice(),
                speed=self.get_selected_speed())
            final_audio = np.concatenate(audio_segments)
            tmp_preview_wav_file = NamedTemporaryFile(suffix='.wav', delete=False)
            soundfile.write(tmp_preview_wav_file, final_audio, core.sample_rate)
            cmd = ['ffplay', '-autoexit', '-nodisp', tmp_preview_wav_file.name]
            subprocess.run(cmd)
            button.SetLabel("🔊 Preview")
            button.Enable()

        if len(self.preview_threads) > 0:
            for thread in self.preview_threads:
                thread.join()
            self.preview_threads = []
        thread = threading.Thread(target=generate_preview)
        thread.start()
        self.preview_threads.append(thread)

    def on_start(self, event):
        self.synthesis_in_progress = True
        file_path = self.selected_file_path
        voice = self.selected_voice.split(' ')[1]  # Remove the flag
        speed = float(self.selected_speed)
        selected_chapters = [chapter for chapter in self.document_chapters if chapter.is_selected]
        self.start_button.Disable()
        self.params_panel.Disable()

        self.table.EnableCheckBoxes(False)
        for chapter_index, chapter in enumerate(self.document_chapters):
            if chapter in selected_chapters:
                self.set_table_chapter_status(chapter_index, "Planned")
                self.table.SetItem(chapter_index, 0, '✔️')

        # self.stop_button.Show()
        print('Starting Audiobook Synthesis', dict(file_path=file_path, voice=voice, pick_manually=False, speed=speed))
        self.core_thread = CoreThread(params=dict(
            file_path=file_path, voice=voice, pick_manually=False, speed=speed,
            output_folder=self.output_folder_text_ctrl.GetValue(),
            selected_chapters=selected_chapters))
        self.core_thread.start()

    def on_open(self, event):
        with wx.FileDialog(self, "Open EPUB File", wildcard="*.epub", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            file_path = dialog.GetPath()
            print(f"Selected file: {file_path}")
            if not file_path:
                print('No filepath?')
                return
            if self.synthesis_in_progress:
                wx.MessageBox("Audiobook synthesis is still in progress. Please wait for it to finish.", "Audiobook Synthesis in Progress")
            else:
                wx.CallAfter(self.open_epub, file_path)

    def on_exit(self, event):
        self.Close()

    def set_table_chapter_status(self, chapter_index, status):
        self.table.SetItem(chapter_index, 3, status)

    def open_folder_with_explorer(self, folder_path):
        try:
            if platform.system() == 'Windows':
                subprocess.Popen(['explorer', folder_path])
            elif platform.system() == 'Linux':
                subprocess.Popen(['xdg-open', folder_path])
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', folder_path])
        except Exception as e:
            print(e)


class CoreThread(threading.Thread):
    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        import core
        core.main(**self.params, post_event=self.post_event)

    def post_event(self, event_name, **kwargs):
        # eg. 'EVENT_CORE_PROGRESS' -> EventCoreProgress, EVENT_CORE_PROGRESS
        EventObject, EVENT_CODE = EVENTS[event_name]
        event_object = EventObject()
        for k, v in kwargs.items():
            setattr(event_object, k, v)
        wx.PostEvent(wx.GetApp().GetTopWindow(), event_object)


def main():
    print('Starting GUI...')
    app = wx.App(False)
    frame = MainWindow(None, "Audiblez - Generate Audiobooks from E-books")
    frame.Show(True)
    frame.Layout()
    app.SetTopWindow(frame)
    print('Done.')
    app.MainLoop()


if __name__ == '__main__':
    main()
