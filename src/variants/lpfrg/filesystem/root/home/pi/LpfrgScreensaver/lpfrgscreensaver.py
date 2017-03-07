#!/usr/bin/python
from __future__ import division

import os
import sys

import pygtk
import gtk, gobject, cairo
from gtk import gdk
import ctypes as ct

import json, yaml, requests

import math
from random import randint
import RPi.GPIO as GPIO
import time

LED_PIN = 22 
PWR_PIN = 11 # Toggles power supply
BUTTON_PIN = 16

BOUNCETIME = 1000 # minimal press interval in ms

FONT_FACE = "/home/pi/LpfrgScreensaver/futura.ttf"
IMAGE_FOLDER = "/home/pi/LpfrgScreensaver/logos/"
OCTOPRINT_CONFIG_PATH = "/home/pi/.octoprint/config.yaml"
JOB_URL = "http://localhost:5000/api/job?apikey={api_key}"
DEFAULT_MODEL = "bolt"
IDLE_STR = "IDLE"
FINISHED_STR = "PRINT FINISHED"

# the secret sauce is to get the "window id" out of $XSCREENSAVER_WINDOW
# code comes from these two places:
# 1) http://pastebin.com/nSCiq1P3
# 2) http://stackoverflow.com/questions/4598581/python-clutter-set-display

#To add: http://stackoverflow.com/questions/7016509/a-way-to-animate-transition-with-python-gtk-and-cairo
# https://cairographics.org/cookbook/animationrotation/



_initialized = False
def create_cairo_font_face_for_file (filename, faceindex=0, loadoptions=0):
    "given the name of a font file, and optional faceindex to pass to FT_New_Face" \
    " and loadoptions to pass to cairo_ft_font_face_create_for_ft_face, creates" \
    " a cairo.FontFace object that may be used to render text with that font."
    global _initialized
    global _freetype_so
    global _cairo_so
    global _ft_lib
    global _ft_destroy_key
    global _surface

    CAIRO_STATUS_SUCCESS = 0
    FT_Err_Ok = 0

    if not _initialized:
        # find shared objects
        _freetype_so = ct.CDLL("libfreetype.so.6")
        _cairo_so = ct.CDLL("libcairo.so.2")
        _cairo_so.cairo_ft_font_face_create_for_ft_face.restype = ct.c_void_p
        _cairo_so.cairo_ft_font_face_create_for_ft_face.argtypes = [ ct.c_void_p, ct.c_int ]
        _cairo_so.cairo_font_face_get_user_data.restype = ct.c_void_p
        _cairo_so.cairo_font_face_set_user_data.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
        _cairo_so.cairo_set_font_face.argtypes = [ ct.c_void_p, ct.c_void_p ]
        _cairo_so.cairo_font_face_status.argtypes = [ ct.c_void_p ]
        _cairo_so.cairo_font_face_destroy.argtypes = (ct.c_void_p,)
        _cairo_so.cairo_status.argtypes = [ ct.c_void_p ]
        # initialize freetype
        _ft_lib = ct.c_void_p()
        status = _freetype_so.FT_Init_FreeType(ct.byref(_ft_lib))
        if  status != FT_Err_Ok :
            raise RuntimeError("Error %d initializing FreeType library." % status)
        #end if

        class PycairoContext(ct.Structure):
            _fields_ = \
                [
                    ("PyObject_HEAD", ct.c_byte * object.__basicsize__),
                    ("ctx", ct.c_void_p),
                    ("base", ct.c_void_p),
                ]
        #end PycairoContext

        _surface = cairo.ImageSurface(cairo.FORMAT_A8, 0, 0)
        _ft_destroy_key = ct.c_int() # dummy address
        _initialized = True
    #end if

    ft_face = ct.c_void_p()
    cr_face = None
    try :
        # load FreeType face
        status = _freetype_so.FT_New_Face(_ft_lib, filename.encode("utf-8"), faceindex, ct.byref(ft_face))
        if status != FT_Err_Ok :
            raise RuntimeError("Error %d creating FreeType font face for %s" % (status, filename))
        #end if

        # create Cairo font face for freetype face
        cr_face = _cairo_so.cairo_ft_font_face_create_for_ft_face(ft_face, loadoptions)
        status = _cairo_so.cairo_font_face_status(cr_face)
        if status != CAIRO_STATUS_SUCCESS :
            raise RuntimeError("Error %d creating cairo font face for %s" % (status, filename))
        #end if
        # Problem: Cairo doesn't know to call FT_Done_Face when its font_face object is
        # destroyed, so we have to do that for it, by attaching a cleanup callback to
        # the font_face. This only needs to be done once for each font face, while
        # cairo_ft_font_face_create_for_ft_face will return the same font_face if called
        # twice with the same FT Face.
        # The following check for whether the cleanup has been attached or not is
        # actually unnecessary in our situation, because each call to FT_New_Face
        # will return a new FT Face, but we include it here to show how to handle the
        # general case.
        if _cairo_so.cairo_font_face_get_user_data(cr_face, ct.byref(_ft_destroy_key)) == None :
            status = _cairo_so.cairo_font_face_set_user_data \
              (
                cr_face,
                ct.byref(_ft_destroy_key),
                ft_face,
                _freetype_so.FT_Done_Face
              )
            if status != CAIRO_STATUS_SUCCESS :
                raise RuntimeError("Error %d doing user_data dance for %s" % (status, filename))
            #end if
            ft_face = None # Cairo has stolen my reference
        #end if

        # set Cairo font face into Cairo context
        cairo_ctx = cairo.Context(_surface)
        cairo_t = PycairoContext.from_address(id(cairo_ctx)).ctx
        _cairo_so.cairo_set_font_face(cairo_t, cr_face)
        status = _cairo_so.cairo_font_face_status(cairo_t)
        if status != CAIRO_STATUS_SUCCESS :
            raise RuntimeError("Error %d creating cairo font face for %s" % (status, filename))
        #end if

    finally :
        _cairo_so.cairo_font_face_destroy(cr_face)
        _freetype_so.FT_Done_Face(ft_face)
    #end try

    # get back Cairo font face as a Python object
    face = cairo_ctx.get_font_face()
    return face
#end create_cairo_font_face_for_file

class Screen(gtk.DrawingArea):
    """ This class is a Drawing Area"""
    def __init__(self):
        super(Screen,self).__init__()
        ## Old fashioned way to connect expose. I don't savvy the gobject stuff.
        self.connect ( "expose_event", self.expose )
        self.connect ( "size-allocate", self.size )
        ## This is what gives the animation life!
        gobject.timeout_add( 50, self.tick ) # Go call tick every 50 whatsits.

    def tick ( self ):
        ## This invalidates the screen, causing the expose event to fire.
        self.alloc = self.get_allocation()
        rect = gtk.gdk.Rectangle(self.alloc.x, self.alloc.y, self.alloc.width, self.alloc.height)
        self.window.invalidate_rect(rect, True)
        return True # Causes timeout to tick again.

    ## When expose event fires, this is run
    def expose(self, widget, event):
        self.cr = self.window.cairo_create()
        self.draw()

class ProgressDisplay(Screen):
    """This class is also a Drawing Area, coming from Screen."""
    def __init__ ( self ):
        Screen.__init__( self )
        self.octoprint_comm = OctoPrintComm()
        self.progress_string = IDLE_STR
        self.image = None
        self.counter = 0
    
    def size(self, widget, event):
        self.screen_w, self.screen_h = self.window.get_size()

        image_path = self.octoprint_comm.get_image_file()

        if image_path:
            self.image = cairo.ImageSurface.create_from_png(image_path)
            self.image_w = self.image.get_width()
            self.image_h = self.image.get_height()
        else:
            self.image_w = 0
            self.image_h = 0

        self.font_face = create_cairo_font_face_for_file(FONT_FACE, 0)
        
        self.counter = 0
        self.fade_duration = 350

        self.image_x = (self.screen_w - self.image_w) / 2
        self.image_y = randint(0, self.screen_h - self.image_h)

        self.text_margin = 20

        self.progress_string = self.octoprint_comm.get_progress_string()
       
    def draw( self ):
        ## A shortcut
        self.cr.set_source_rgba(0.0, 0.0, 0.0, 1)
        self.cr.rectangle(0, 0, self.screen_w, self.screen_h)
        self.cr.fill()

        if self.counter < self.fade_duration:
            self.drawProgress(self.cr, self.counter / self.fade_duration)
            if self.image:
                self.drawImage(self.cr, self.counter / self.fade_duration)
            
        
        self.counter += 1

        if self.counter >= self.fade_duration:
            self.progress_string = self.octoprint_comm.get_progress_string()
            self.image_y = randint(0, self.screen_h - self.image_h)
            self.counter = 0
       
    def drawProgress(self, cr, progress):
        cr.set_source_rgba(1, 1, 1, self.getAlpha(progress))
        cr.set_font_face(self.font_face)
        cr.set_font_size(45)
        
        (x, y, width, height, dx, dy) = cr.text_extents(self.progress_string)
        cr.move_to(self.image_x + (self.image_w - width)/2, self.image_y + self.image_h + height + self.text_margin)    
        cr.show_text(self.progress_string)


    def drawImage ( self, cr, progress):
        cr.set_source_surface(self.image, self.image_x, self.image_y)
        cr.rectangle( self.image_x, self.image_y, self.image_w, self.image_h )
        cr.clip()
        alpha = self.getAlpha(progress)
        cr.paint_with_alpha(alpha)

    def getAlpha(self, progress):
        if progress <= 0.2:
            return 5*progress
        elif progress <= 0.8:
            return 1
        else:
            return 5 * (1-progress)

class ScreenSaverWindow(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self)
        self.screen_w = 600
        self.screen_h = 1024

    def realize(self):
        if self.flags() & gtk.REALIZED:
            return

        ident = os.environ.get('XSCREENSAVER_WINDOW')
        if not ident is None:
            self.window = gtk.gdk.window_foreign_new(int(ident, 16))
            self.window.set_events (gdk.EXPOSURE_MASK | gdk.STRUCTURE_MASK)
            
            x, y, w, h, depth = self.window.get_geometry()
            self.size_allocate(gtk.gdk.Rectangle(x, y, w, h))
            self.set_default_size(w, h)
            self.set_decorated(False)

            self.window.set_user_data(self)
            self.style.attach(self.window)

        if self.window == None:
            self.window = gdk.Window(None, self.screen_w, self.screen_h, gdk.WINDOW_TOPLEVEL,
                                     (gdk.EXPOSURE_MASK | gdk.STRUCTURE_MASK),
                                     gdk.INPUT_OUTPUT)
 
            self.set_default_size(self.screen_w, self.screen_h)
            self.set_decorated(False)   
            self.window.set_user_data(self)       
            self.style.attach(self.window)  

        if self.window != None:
            self.set_flags(self.flags() | gtk.REALIZED)

class OctoPrintComm():
    def __init__(self):
        self.config_data = None
        self.api_key = self._read_api_key()
        self.model = self._read_model()
        self.job_url = JOB_URL.format(api_key=self.api_key)

    # Public methods
    def get_progress_string(self):
        job = self._get_job_data()

        if job and "state" in job and "progress" in job:
            if job["state"] == "Operational" and job["progress"]["completion"] == 100:
                return FINISHED_STR
            elif job["state"] == "Printing":
                return "{0:.0f}%".format(job["progress"]["completion"])
        
        return IDLE_STR

    def get_image_file(self):
        if self.model:
            path = os.path.join(IMAGE_FOLDER, self.model + ".png")
            if os.path.exists(path):
                return path

    # Private methods
    def _read_config(self):
        if os.path.exists(OCTOPRINT_CONFIG_PATH):
            with open(OCTOPRINT_CONFIG_PATH, "rb") as fp:
                self.config_data = yaml.safe_load(fp)
    
    def _read_api_key(self):
        if not self.config_data:
            self._read_config()

        if self.config_data and "api" in self.config_data and "key" in self.config_data["api"]:
            return self.config_data["api"]["key"]

    def _read_model(self):
        if not self.config_data:
            self._read_config()

        if self.config_data and "plugins" in self.config_data and "lui" in self.config_data["plugins"] and "model" in self.config_data["plugins"]["lui"]:
            return self.config_data["plugins"]["lui"]["model"].lower()
        else:
            return DEFAULT_MODEL

    def _get_job_data(self):
        try:
            response = requests.get(self.job_url)
        except:
            return None
        
        if response.status_code == 200:
            try:
                return response.json()
            except:
                return None
       
        

window = ScreenSaverWindow()
window.set_title('Floaters')
window.set_default_size(600, 1024)
window.realize()

window.modify_bg(gtk.STATE_NORMAL, gdk.color_parse("black"))

window.connect( "delete-event", gtk.main_quit )
widget = ProgressDisplay()
widget.show()
window.add(widget)
window.present()

def shutdown_button_press(c):
    import subprocess
    subprocess.call("xscreensaver-command -deactivate".split())
    
GPIO.setmode(GPIO.BOARD)
GPIO.setup(BUTTON_PIN, GPIO.IN)
GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=shutdown_button_press, bouncetime=BOUNCETIME)

gtk.main()
