# -*- coding: utf-8 -*-
#!/usr/bin/python

import hal
import glib
import time
import gtk
import linuxcnc
import os
import json

class HandlerClass:
    '''
    class with gladevcp callback handlers
    '''

    # типы фрезеровки в combobox
    milling_types = ["diagonal", "diagonalRL", "perforation",
    "transverse", "cone"]

    # ссылки на шаблоны  GCode
    templates_list = ["template_diagonal.txt", "template_diagonalRL.txt",
        "template_perforation.txt", "template_transverse.txt", "template_cone.txt"]   

    # ссылки на изображения со схемой для каждого типа фрезеровки
    image_list = ["img_diagonal.png", "img_diagonalRL.png",
        "img_perforation.png", "img_transverse.png", "img_cone.png"]

    # список элементов управления, которые активны для пазов разной формы
    active_control_list = {
        "diagonal":["spnWD", "spnWd", "spn_alpha",
                    "spnS", "spn_d", "spn_p2"],
        "diagonalRL":["spnWD", "spnWd", "spn_alpha",
                    "spnS", "spn_d", "spn_p2"],
        "perforation":["spnS", "spn_d"],
        "transverse":["spnWD", "spnWd","spnS", "spn_d", "spn_p2"],
        "cone":["spnS", "spn_d", "spnD"],
        "all":["spnWD", "spnWd", "spn_d", "spn_alpha",
        "spnS", "spn_p2", "spnD"] }

    replacement_list = {
        "diagonal":[]
        "diagonalRL":[],
        "perforation":[],
        "transverse":[],
        "cone":[],
    }

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
        milling_type_number = index[1]  # строка с названием типа обработки (см. модель, Glade *.ui файл)
        milling_type = index[2]         # строка с названием типа обработки (см. модель, Glade *.ui файл)

        print "*** index[0]=", index[0] , ", index[1]=", index[1], ", index[2]=", index[2]
        print "*** milling_type_number = ", milling_type_number

        # переключить изображение схемы обработки
        imgDrawing = self.builder.get_object('imgDrawing')
        imgDrawing = imgDrawing.set_from_file(self.image_list[milling_type_number])
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
                
        return
    
    def on_btnSave_clicked(self,widget):
        '''
        Обработчик нажатия кнопки сохранения программы обработки. Подставляет в шаблон,
        соответствующий типу фрезеровки, параметры из GUI, сохраняет под именем,
        выбранным в диалоговом окне и загружает в AXIS
        '''

        window1 = self.builder.get_object('window1')

        cmbMillType = self.builder.get_object('cmbMillType') # ссылка combobox 'cmbMillType', в котором выбирается тип фрезеровки
        item = cmbMillType.get_active_iter() # ссылка на выбранный элкмент в combobox

        if item is None:
            #TODO отображать диалоговое окно с предупреждением о том, что некорректный тип обработки
            return

        "spnNumber"
        "spn_alpha"
        
        "spnLength"
        "wpnWidth"
        "spnWd"
        "spnWD"
        "spn_d"
        "spnD"
        "spnS"
        "spn_p2"

        model = cmbMillType.get_model()
        index = model[item]
        milling_type_number = index[1]  # строка с названием типа обработки (см. модель, Glade *.ui файл)
        milling_type = index[2]         # строка с названием типа обработки (см. модель, Glade *.ui файл)

        
        #чтение шаблона
        f1 = open(self.templates_list[milling_type_number],'rb')
        filedata1 = f1.read()
        f1.close()
        
        # print "\nФайл 1\n=========================="
        # print filedata1
        
        # f2 = open("Фрезерование паза с комментриями.ngc",'rb')
        # filedata2 = f2.read()
        # f2.close()
        
        # print "\nФайл 2\n=========================="
        # print filedata2

        #["Сверление с комментариями.ngc", "Фрезерование паза с комментриями.ngc"]
        #замена
        replacements = [["#<_i>",],
            ["#<_N>",],
            ["#<_alpha>",],
            ["#<_beta>",],
            ["#<_beta>",],
            ["#<_F>",]]
        
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
            #f.close()
        finally :
            filechooserdialog.destroy()
        
        #TODO создание и запись нового файла когда будут готовы шаблоны
        #configfile = codecs.open(filename,'ab+','utf-8')
        #config.write(configfile)
        #configfile.close()
        return
    
    def on_btnSaveAndOpen_clicked(self, widget):
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
        os.system("axis-remote " + filename)
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
