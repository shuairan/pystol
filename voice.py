#!/usr/bin/env python

# Copyright (c) 2008 Carnegie Mellon University.
#
# You may modify and redistribute this file under the same terms as
# the CMU Sphinx system.  See
# http://cmusphinx.sourceforge.net/html/LICENSE for more information.

import pygtk
pygtk.require('2.0')
import gtk

import gobject
import pygst
pygst.require('0.10')
gobject.threads_init()
import gst

import sys
import os
import webcolors

"""Helpers:"""


COLORS = {  'red'   : (255, 0, 0),
            'lime'  : (0, 255, 0),
            'green' : (0, 128, 0),
            'blue'  : (0, 0, 255) ,
            'white' : (255, 255, 255) ,
            'black' : (0, 0, 0) ,
            'yellow': (255, 255, 0) ,
            'aqua'  : (0, 255, 255) ,
            'orange': (255, 165, 0) ,
            'navy'  : (0, 0, 128) ,
            'purple': (128, 0, 128) ,
            'magenta':(255, 0, 255) ,
            'indigo': (75, 0, 130) ,
            'gray'  : (128, 128, 128),
            'grey'  : (128, 128, 128),
            'fuchsia':(255, 0, 255),
            'maroon': (128, 0, 0),
            'olive' : (128, 128, 0),
            'silver': (192, 192, 192),
            'teal'  : (0, 128, 128)
         }
         
def getColor(name, default=(0, 0, 0)):
    name = name.lower()
    if name in COLORS:
        return COLORS[name]
    else:
        return default
        
def sendColor(color):
    os.popen("ola_set_dmx -u 1 -d %s,%s,%s,0,0,0,%s,%s,%s,0,0,0" % color)


class VoiceControl(object):
    """GStreamer/PocketSphinx Demo Application"""
    def __init__(self, parent):
        """Initialize a DemoApp object"""
        self.init_gui(parent)
        self.init_gst()
        self.lastmsg = ""
        
    def init_gui(self, parent):
        """Initialize the GUI components"""
        vbox = gtk.VBox()
        self.textbuf = gtk.TextBuffer()
        self.text = gtk.TextView(self.textbuf)
        self.text.set_wrap_mode(gtk.WRAP_WORD)
        vbox.pack_start(self.text)
        self.button = gtk.ToggleButton("Speak")
        self.button.connect('clicked', self.button_clicked)
        vbox.pack_start(self.button, False, False, 5)
        parent.add(vbox)
        parent.show_all()

    def init_gst(self):
        """Initialize the speech components"""
        self.pipeline = gst.parse_launch('gconfaudiosrc ! audioconvert ! audioresample '
                                         + '! vader name=vad auto-threshold=true '
                                         + '! pocketsphinx name=asr ! fakesink')
        asr = self.pipeline.get_by_name('asr')
        asr.connect('partial_result', self.asr_partial_result)
        asr.connect('result', self.asr_result)
        asr.set_property('configured', True)
        
        asr.set_property('lm', 'voice/4725.lm')
        asr.set_property('dict', 'voice/4725.dic')
        
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::application', self.application_message)

        self.pipeline.set_state(gst.STATE_PAUSED)

    def asr_partial_result(self, asr, text, uttid):
        """Forward partial result signals on the bus to the main thread."""
        struct = gst.Structure('partial_result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        asr.post_message(gst.message_new_application(asr, struct))

    def asr_result(self, asr, text, uttid):
        """Forward result signals on the bus to the main thread."""
        struct = gst.Structure('result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        asr.post_message(gst.message_new_application(asr, struct))

    def application_message(self, bus, msg):
        """Receive application messages from the bus."""
        msgtype = msg.structure.get_name()
        if msgtype == 'partial_result':
            self.partial_result(msg.structure['hyp'], msg.structure['uttid'])
        elif msgtype == 'result':
            self.final_result(msg.structure['hyp'], msg.structure['uttid'])
            #self.pipeline.set_state(gst.STATE_PAUSED)
            #self.button.set_active(False)
            
    def partial_result(self, hyp, uttid):
        """Delete any previous selection, insert text and select it."""
        # All this stuff appears as one single action
        self.textbuf.begin_user_action()
        self.textbuf.delete_selection(True, self.text.get_editable())
        self.textbuf.insert_at_cursor(hyp)
        ins = self.textbuf.get_insert()
        iter = self.textbuf.get_iter_at_mark(ins)
        iter.backward_chars(len(hyp))
        self.textbuf.move_mark(ins, iter)
        self.textbuf.end_user_action()

    def final_result(self, hyp, uttid):
        """Insert the final result."""
        # All this stuff appears as one single action
        self.textbuf.begin_user_action()
        self.textbuf.delete_selection(True, self.text.get_editable())
        self.textbuf.insert_at_cursor(hyp)
        self.textbuf.end_user_action()

        if str(self.lastmsg)=="COMPUTER":
            color = getColor(hyp)
            sendColor(color + color) 
        self.lastmsg = hyp
        
    def button_clicked(self, button):
        """Handle button presses."""
        if button.get_active():
            button.set_label("Stop")
            self.pipeline.set_state(gst.STATE_PLAYING)
        else:
            button.set_label("Speak")
            self.pipeline.set_state(gst.STATE_PAUSED)
            vader = self.pipeline.get_by_name('vad')
            vader.set_property('silent', True)
