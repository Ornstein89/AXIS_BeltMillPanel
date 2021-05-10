# -*- coding: utf-8 -*-
#!/usr/bin/python

import hal
import glib
import time
import gtk
import linuxcnc
import os
import json
import io
import math
import configparser

class HandlerClass:
    '''
    class with gladevcp callback handlers
    '''

    config_file_name = "AXIS_BeltMillPanelSetting.cfg"

    # типы фрезеровки в combobox
    milling_types = ["diagonal", "diagonal_rl", "perforation",
    "transverse", "cone"]

    # ссылки на шаблоны  GCode
    templates_list = {"diagonal":"template_diagonal.txt",
                    "diagonal_rl":"template_diagonal_rl.txt",
        "perforation":"template_perforation.txt",
        "transverse":"template_diagonal.txt", # тот же шаблон, что для диагональной, но alpha = 90
        "cone":"template_perforation.txt"} # тот же шаблон, что для сверления

    prev_milling_type = "default"

    # ссылки на изображения со схемой для каждого типа фрезеровки
    # image_list = ["img_diagonal.png", "img_diagonalRL.png",
    #     "img_perforation.png", "img_transverse.png", "img_cone.png"]

    # список элементов управления, которые активны для пазов разной формы
    # имена должны соответствовать именам в файле *.ui
    # имена также используются с фигурными скобками для подстановки параметров в шаблоны
    active_control_list = {
        "diagonal"   :["spnWD", "spnWd", "spn_alpha", "spnS", "spn_d", "spn_p2", "spnNumber",
                       "spnLength", "spnWidth"], # также {parameter_beta}
        "diagonal_rl":["spnWD", "spnWd", "spn_alpha", "spnS", "spn_d", "spn_p2", "spnNumber",
                       "spnLength", "spnWidth"], # также {parameter_beta}
        "perforation":["spnS", "spn_d", "spnLength", "spnWidth"],
        "transverse" :["spnWD", "spnWd", "spnS", "spn_d", "spn_p2", "spnLength", "spnWidth"],
        "cone"       :["spnS", "spn_d", "spnD", "spnLength", "spnWidth"],
        "all"        :["spnWD", "spnWd", "spn_d", "spn_alpha", "spnS", 
                       "spn_p2", "spnD", "spnLength", "spnWidth"] }

    def on_cmbMillType_changed(self, widget, data=None):
        '''
        a callback method
        parameters are:
            the generating object instance, likte a GtkButton instance
            user data passed if any - this is currently unused but
            the convention should be retained just in case
        '''
        #DEBUG print "*** on_cmbMillType_changed"

        cmbMillType = self.builder.get_object('cmbMillType') # ссылка combobox 'cmbMillType', в котором выбирается тип фрезеровки
        item = cmbMillType.get_active_iter() # ссылка на выбранный элкмент в combobox

        if item is None:
            #TODO отображать диалоговое окно с предупреждением о том, что некорректный тип обработки
            return

        model = cmbMillType.get_model()
        index = model[item]
        milling_type_number = index[1]  # порядковый номер типа обработки (см. модель, Glade *.ui файл)
        milling_type = index[2]         # строка с названием типа обработки (см. модель, Glade *.ui файл)

        # включение alpha=90 градусов в интерфейсе для поперечного типа фрезеровки
        # если произошла смена с любого типа на поперечный
        if (milling_type == "transverse") and (self.prev_milling_type != "transverse"):
            spnAlpha = self.builder.get_object("spnAlpha")
            self.alpha = spnAlpha.get_value()
            spnAlpha.set_value(90.0)
        
        # если произошла обратная смена
        if (milling_type != "transverse") and (self.prev_milling_type == "transverse"):
            spnAlpha = self.builder.get_object("spnAlpha")
            spnAlpha.set_value(self.alpha)       

        print "*** index[0]=", index[0] , ", index[1]=", index[1], ", index[2]=", index[2]
        print "*** milling_type_number = ", milling_type_number

        # переключить изображение схемы обработки
        imgDrawing = self.builder.get_object('imgDrawing')
        imgDrawing = imgDrawing.set_from_file("img_"+milling_type+".png")
        #pixbuf = gtk.gdk.new_from_file_at_scale(image_list[milling_type_number], 400, 800, True)
        #pixbuf = gtk.gdk.GdkPixbuf.Pixbuf.new_from_file_at_scale(image_list[milling_type_number], 400, 800, True)
        #pixbuf = gtk.gdk.Pixbuf.new_from_file_at_scale(image_list[milling_type_number], 400, 800, True)
        #imgDrawing = imgDrawing.set_from_pixbuf(pixbuf)
        
        # деактивировать неиспользуемые для данного milling_type поля ввода
        for control_name in self.active_control_list["all"]:
            if control_name in self.active_control_list[milling_type]:
                self.builder.get_object(control_name).set_sensitive(True)
            else:
                self.builder.get_object(control_name).set_sensitive(False)

        self.prev_milling_type = milling_type
                
        return
    
    def save_settings(self):
        # https://cpython-test-docs.readthedocs.io/en/latest/library/configparser.html
        config_obj = configparser.ConfigParser(strict=False)
        config_obj["DEFAULT"] = {}
        for cnt_name in self.active_control_list["all"]:
            input_field = self.builder.get_object(cnt_name)
            config_obj["DEFAULT"][cnt_name] = input_field.get_value()
        
        if self.prev_milling_type == "transverse":
            config_obj["DEFAULT"]["spn_alpha"] = self.alpha

        config_file = io.open(self.config_file_name, 'w', encoding='utf8')
        config_obj.write(config_file)
        config_file.close()
        return

    def load_settings(self):
        # https://cpython-test-docs.readthedocs.io/en/latest/library/configparser.html
        config = configparser.ConfigParser(strict=False)
        try:
            config.read(self.config_file_name)
        except:
            return
        
        if "DEFUALT" not in config:
            return
        
        for key in config["DEFUALT"]:
            try:
                input_field = self.builder.get_object(key)
                input_field.set_value(config["DEFUALT"][key])
            except:
                continue
        return

    def save_file(self):
        window1 = self.builder.get_object('window1')
        cmbMillType = self.builder.get_object('cmbMillType') # ссылка combobox 'cmbMillType', в котором выбирается тип фрезеровки
        item = cmbMillType.get_active_iter() # ссылка на выбранный элкмент в combobox

        if item is None:
            #TODO отображать диалоговое окно с предупреждением о том, что некорректный тип обработки
            return None

        model = cmbMillType.get_model()
        index = model[item]
        milling_type_number = index[1]  # порядковый номер типа обработки (см. модель, Glade *.ui файл)
        milling_type = index[2]         # строка с названием типа обработки (см. модель, Glade *.ui файл)

        
        #чтение шаблона
        template_file_name = "template_"+milling_type+".txt"
        try:
            templatefile = io.open(template_file_name,'r', encoding='utf8')
            templatedata = templatefile.read()
            templatefile.close()
        except Exception as e:
            #TODO отображать диалоговое окно с предупреждением о том, что нет файла шаблона
            print "ERROR: ошибка при открытии файла ", template_file_name, ", исключение ", e
            return None
        
        # подсчёт параметра parameter_beta = шаг * 180/3.1415 * радиус шкива
        radius = 200.0; #TODO радиус шкива, уточнить
        parameter_beta = math.radians(self.builder.get_object("spnS").get_value()/radius)

        # замена
        for control_name in self.active_control_list[milling_type]:
            input_field = self.builder.get_object(control_name)
            #DEBUG print dir(input_field)
            #DEBUG print "*** input_field.get_value() = ", str(input_field.get_value())
            #DEBUG value = input_field.get_value_as_int()
            value = input_field.get_value()
            templatedata.replace("{" + control_name + "}",  u"%0.2f" % value)
        
        #https://python-gtk-3-tutorial.readthedocs.io/en/latest/dialogs.html
        #https://github.com/cnc-club/linuxcnc-features/blob/master/features.py
        filechooserdialog = gtk.FileChooserDialog(
            "Сохранить файл программы", window1,
            gtk.FILE_CHOOSER_ACTION_SAVE,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_OK, gtk.RESPONSE_OK))#, action=gtk.FileChooserAction.OPEN
        filename = []
        try :
            filt = gtk.FileFilter()
            filt.set_name("NGC")
            filt.add_mime_type("text/ngc")
            filt.add_pattern("*.ngc")
            filechooserdialog.add_filter(filt)
            #filechooserdialog.set_current_folder(APP_PATH + NGC_DIR)

            response = filechooserdialog.run()
            print "***response = ", response
            if response == gtk.RESPONSE_OK:
                #gcode = self.to_gcode()
                filename = filechooserdialog.get_filename()
                if filename[-4] != ".ngc" not in filename :
                    filename += ".ngc"
                #f = open(filename, "w")
                #f.write(gcode)
                print "*** filename = ", filename
        except Exception as e:
            #TODO уведомление
            print "ERROR: ошибка при открытии диалога выбора файла, исключение ", e
            return None
            #f.close()
        finally :
            filechooserdialog.destroy()
        
        try:
            newfile = io.open(filename, "w", encoding='utf8')
            newfile.write(templatedata)
            newfile.close()
        except Exception as e:
            #TODO уведомление
            print "ERROR: ошибка при записи файла ", filename, ", исключение ", e
            return None
        
        #TODO создание и запись нового файла когда будут готовы шаблоны
        #configfile = codecs.open(filename,'ab+','utf-8')
        #config.write(configfile)
        #configfile.close()
        return filename
    
    def on_btnSave_clicked(self,widget):
        '''
        Обработчик нажатия кнопки сохранения программы обработки. Подставляет в шаблон,
        соответствующий типу фрезеровки, параметры из GUI, сохраняет под именем,
        выбранным в диалоговом окне (при этом НЕ загружает файл в AXIS)
        '''
        self.save_file()

        return
    
    def on_btnSaveAndOpen_clicked(self, widget):
        '''
        Обработчик нажатия кнопки сохранения программы обработки. Подставляет в шаблон,
        соответствующий типу фрезеровки, параметры из GUI, сохраняет под именем,
        выбранным в диалоговом окне и загружает в AXIS
        '''
        filename = self.save_file()
        if filename is None:
            return
        os.system("axis-remote " + filename)

        #TODO сохранение
        
        #print "*** on_btnSaveAndOpen_clicked"
        #dir_path = os.path.dirname(os.path.realpath(__file__))
        #print "*** dir_path = ", dir_path
        #print "*** os.getcwd() = ", os.getcwd()
        #lxcnc = linuxcnc.command()
        #lxcnc.mode(linuxcnc.MODE_MDI)
        
        # загрузка сохранённого файла
        # https://www.forum.linuxcnc.org/41-guis/34454-python-open-ngc
        filename = "sample.ngc"
        #lxcnc.program_open(filename)
        #os.system("axis-remote --reload ")
        
        #lxcnc.mode(linuxcnc.MODE_MANUAL)
        return

    def __init__(self, halcomp,builder,useropts):
        '''
        Handler classes are instantiated in the following state:
        - the widget tree is created, but not yet realized (no toplevel window.show() executed yet)
        - the halcomp HAL component is set up and the widhget tree's HAL pins have already been added to it
        - it is safe to add more hal pins because halcomp.ready() has not yet been called at this point.

        after all handlers are instantiated in command line and get_handlers() order, callbacks will be
        connected with connect_signals()/signal_autoconnect()

        The builder may be either of libglade or GtkBuilder type depending on the glade file format.
        '''

        self.halcomp = halcomp
        self.builder = builder
        self.nhits = 0
        return

def get_handlers(halcomp,builder,useropts):
    '''
    this function is called by gladevcp at import time (when this module is passed with '-u <modname>.py')

    return a list of object instances whose methods should be connected as callback handlers
    any method whose name does not begin with an underscore ('_') is a  callback candidate

    the 'get_handlers' name is reserved - gladevcp expects it, so do not change
    '''
    return [HandlerClass(halcomp,builder,useropts)]
