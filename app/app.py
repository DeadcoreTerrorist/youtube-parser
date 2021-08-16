from PyQt5.QtWidgets import QFileDialog, QDialog
from PyQt5 import QtWidgets
from pytube import YouTube
from views.design import Ui_MainWindow
import pytube
import re
import pafy
from pytube.exceptions import RegexMatchError, VideoUnavailable


class YoutubeParser(Ui_MainWindow, QDialog):
    def add_functions(self):
        self.find_button.clicked.connect(lambda: self.find_video())
        self.only_audio_check.clicked.connect(lambda: self. audio_status_changed())
        self.only_video_check.clicked.connect(lambda: self.video_status_changed())
        self.download_mp4_button.clicked.connect(lambda: self.download_video())
        self.cancel_video_button.clicked.connect(lambda: self.cancel_button())
        self.show_subtitles_button.clicked.connect(lambda: self.make_subtitles())
        self.download_subtitles_button.clicked.connect(lambda: self.download_subtitles())

    def __enable_download_buttons(self, *args):
        self.link_line.setEnabled(args[0])
        self.find_button.setEnabled(args[1])
        self.quality_box.setEnabled(args[2])
        self.download_mp4_button.setEnabled(args[3])
        self.only_audio_check.setEnabled(args[4])
        self.only_video_check.setEnabled(args[5])
        self.cancel_video_button.setEnabled(args[6])

    def __enable_subtitles_buttons(self, *args):
        self.column_check.setEnabled(args[0])
        self.pick_language_box.setEnabled(args[1])
        self.show_subtitles_button.setEnabled(args[2])
        self.download_subtitles_button.setEnabled(args[3])

    def find_video(self):
        try:
            if self.only_audio_check.isChecked():
                self.__get_video(only_audio=True)
            elif self.only_video_check.isChecked():
                self.__get_video(only_video=True)
            else:
                self.__get_video()
        except RegexMatchError:
            self.cancel_button()
            self.link_line.setPlaceholderText('Wrong input! Try again')
        except VideoUnavailable:
            self.cancel_button()
            self.link_line.setPlaceholderText('Unavailable video! Try again')
        except:#for other cases
            self.cancel_button()

    def __get_video(self, only_audio=False, only_video=False):
        self.__enable_download_buttons(False, False, True, True, False, False, True)

        if only_audio:#defining self.video
            self.video = pafy.new(self.link_line.text())
        else:
            self.video = pytube.YouTube(self.link_line.text())

        if only_video:#defining self.video_streams
            self.video_streams = self.video.streams.filter(only_video=True).desc()
        elif only_audio:
            self.video_streams = self.video.audiostreams
        else:
            self.video_streams = self.video.streams.filter(progressive=True).desc()#progressive - video and audio only

        if only_audio:#defining quality_list
            self.quality_list = list(set(re.findall(r'audio:(.{3,4})(?=@)', str(self.video_streams))))
        else:
            self.quality_list = list(set(re.findall(r'[0-9]{1,4}p', str(self.video_streams))))

        self.quality_box.addItems(self.quality_list)

        self.subtitles_langs = YouTube(self.link_line.text()).captions#working with subtitles
        if self.subtitles_langs != '{}':
            self.__enable_subtitles_buttons(True, True, True, True)
            self.pick_language_box.addItems(re.findall(r'code=\"(.{2,4})\"', str(self.subtitles_langs)))

    def download_video(self):
        if self.only_audio_check.isChecked():
            self.__download_process(only_audio=True)
        elif self.only_video_check.isChecked():
            self.__download_process(only_video=True)
        else:
            self.__download_process()

    def __download_process(self, only_audio=False, only_video=False):
        self.video_path = QFileDialog.getSaveFileName(self)[0]
        if only_audio:
            self.video.getbestaudio().download(f'{self.video_path}.{self.quality_box.currentText()}')
        else:
            try:
                self.picked_stream = self.video_streams.filter(only_video=only_video, res=self.quality_box.currentText()).first()
                self.video_folder = re.findall(r'.+(?=/.+$)', self.video_path)[0]  # directory/folder
                self.filename = f"{re.findall(r'/.+/(.+?)$', self.video_path)[0]}.mp4"  # file.mp4
                self.picked_stream.download(self.video_folder, filename=self.filename)
            except IndexError:#if video_path was not pointed out
                self.cancel_button()
                self.link_line.setPlaceholderText('Wrong folder! Tru again')
        self.cancel_button()

    def audio_status_changed(self):
        if self.only_video_check.isChecked():
            self.only_video_check.setChecked(False)

    def video_status_changed(self):
        if self.only_audio_check.isChecked():
            self.only_audio_check.setChecked(False)

    def cancel_button(self):
        self.__enable_download_buttons(True, True, False, False, True, True, True)
        self.__enable_subtitles_buttons(False, False, False, False)
        self.link_line.clear()
        self.link_line.setPlaceholderText('Input URL of the video here and press find')
        self.quality_box.clear()
        self.pick_language_box.clear()
        self.only_audio_check.setChecked(False)
        self.only_video_check.setChecked(False)
        self.subtitles_area.clear()

    def make_subtitles(self, to_show=True):
        self.xml_subtitles = self.subtitles_langs.get_by_language_code(self.pick_language_box.currentText()).xml_captions

        if len(self.pick_language_box.currentText()) == 4:#there are two types of lang. codes: en and a.en. The difference is that first one are automatic subtitles and other one is note
            self.subtitles = re.findall(r'ac="[0-9]{1,5}"> (.+?(?=</s>))', self.xml_subtitles, re.DOTALL)#for automatic subtitles, pay attention on space in regular expression
        else:
            self.subtitles = re.findall(r'd="[0-9]{1,5}">(.+?(?=</p>))', self.xml_subtitles, re.DOTALL)

        if self.column_check.isChecked():
            self.subtitles_to_show = '\n'.join(self.subtitles).replace('&#39;', '')
        else:
            self.subtitles_to_show = " ".join(self.subtitles).replace('&#39;', '')

        if to_show:
            self.subtitles_area.setText(self.subtitles_to_show)

    def download_subtitles(self):
        self.subtitles_path = QFileDialog.getSaveFileName(self)[0]
        with open(f'{self.subtitles_path}.txt', 'w') as file:
            self.make_subtitles(False)#if subtitles_to_show was not defined before download button is pressed
            file.write(self.subtitles_to_show)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    MainWindow = QtWidgets.QMainWindow()
    ui = YoutubeParser()
    ui.setupUi(MainWindow)
    ui.add_functions()
    MainWindow.show()
    sys.exit(app.exec_())