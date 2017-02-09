#!/usr/bin/python

import os
import sys

import pygtk
import gtk, gobject, cairo
from gtk import gdk

import math
from random import randint

IMAGE_PATH = "/home/pi/LpfrgScreensaver/lpfrg.png"

# the secret sauce is to get the "window id" out of $XSCREENSAVER_WINDOW
# code comes from these two places:
# 1) http://pastebin.com/nSCiq1P3
# 2) http://stackoverflow.com/questions/4598581/python-clutter-set-display

#To add: http://stackoverflow.com/questions/7016509/a-way-to-animate-transition-with-python-gtk-and-cairo
# https://cairographics.org/cookbook/animationrotation/

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

class Frog(Screen):
    """This class is also a Drawing Area, coming from Screen."""
    def __init__ ( self ):
        Screen.__init__( self )
    
    def size(self, widget, event):
        self.screen_w, self.screen_h = self.window.get_size()

        self.delta = 5

        self.image = cairo.ImageSurface.create_from_png(IMAGE_PATH);
        
        self.image_w = self.image.get_width()
        self.image_h = self.image.get_height()

        self.image_x = randint(0, self.screen_w - self.image_w)
        self.image_y = randint(0, self.screen_h - self.image_h)

        self.image_ang = randint(0, 359)
       
    def draw( self ):
        ## A shortcut
        self.cr.set_source_rgba(0.0, 0.0, 0.0, 1)
        self.cr.rectangle(0, 0, self.screen_w, self.screen_h)
        self.cr.fill()
        self.drawFrog(self.cr)

        self.image_x += self.delta * math.cos(math.radians(self.image_ang))
        self.image_y += self.delta * math.sin(math.radians(self.image_ang))
       
        self.norm_ang = 0
        if self.image_x + self.image_w >= self.screen_w:
            # right bounce
            self.norm_ang = 180
            self.image_ang = 2 * self.norm_ang - 180 - self.image_ang
        elif self.image_x <= 0:
            # left bounce
            self.norm_ang = 0
            self.image_ang = 2 * self.norm_ang - 180 - self.image_ang
        elif self.image_y + self.image_h >= self.screen_h:
            # Bottom bounce
            self.norm_ang = 90
            self.image_ang = 2 * self.norm_ang - 180 - self.image_ang
        elif self.image_y <= 0:
            # Top bounce
            self.norm_ang = 270
            self.image_ang = 2 * self.norm_ang - 180 - self.image_ang

    def drawFrog ( self, cr ):
        cr.set_source_surface(self.image, self.image_x, self.image_y)
        cr.rectangle( self.image_x, self.image_y, self.image_w, self.image_h )
        cr.clip()
        cr.paint()

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

window = ScreenSaverWindow()
window.set_title('Floaters')
window.set_default_size(600, 1024)
window.realize()

window.modify_bg(gtk.STATE_NORMAL, gdk.color_parse("black"))

window.connect( "delete-event", gtk.main_quit )
widget = Frog()
widget.show()
window.add(widget)
window.present()

gtk.main()
