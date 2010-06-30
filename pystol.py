#!/usr/bin/env python

import sys
import math
import impulse
try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk
    import gtk.glade
except:
    sys.exit(1)
import gobject



peak_heights = [ 0 for i in range( 256 ) ]
peak_acceleration = [ 0.0 for i in range( 256 ) ]

bar_color = ( 0.0, 0.6, 1.0, 0.8 )
peak_color = ( 1.0, 0.0, 0.0, 0.8 )

n_cols = 10
col_width = 16
col_spacing = 1

n_rows = 50
row_height = 5
row_spacing = 1



class PystolGTK:
    """This is an Hello World GTK application"""

    def __init__(self):
    
        #Set the Glade file
        self.builder = gtk.Builder()
        self.gladefile = "./glade/pystol.glade"  
        self.builder.add_from_file(self.gladefile)
        
        #builder.connect_signals(anobject)
        #builder.get_object(name)
        self.window = self.builder.get_object("PyStoL")
        self.builder.connect_signals(self)
        
        self.spectrumArea = self.builder.get_object("analyzer")
        gtk.DrawingArea.__init__(self.spectrumArea)
        self.spectrumArea.connect("expose-event", self.expose)
        
        self.timer = gobject.timeout_add( 33, self.update )

    def update (self):

        self.redraw_canvas()
        return True # keep running this event
    
    def redraw_canvas (self):
        if self.window.window:
            alloc = self.spectrumArea.get_allocation()
            #rect = gdk.Rectangle(alloc.x, alloc.y, alloc.width, alloc.height)
            #self.window.invalidate_rect(rect, True)
            #self.spectrumArea.queue_draw_area(alloc.x, alloc.y, alloc.width, alloc.height)
            self.spectrumArea.queue_draw_area(0, alloc.y, alloc.width, alloc.height)
            self.window.window.process_updates(True)


    def expose(self, widget, event):
        self.context = self.spectrumArea.window.cairo_create()
        
        # set a clip region for the expose event
        self.context.rectangle(event.area.x, event.area.y,
                               event.area.width, event.area.height)
        #print "Expose:", event.area.x, event.area.y, event.area.width, event.area.height
        self.context.clip()
        
        self.draw(self.context)
        
        return False
    
    def draw(self, cr):
        rect =  self.spectrumArea.get_allocation()
        
        #print "Print:",  rect.x, rect.y, rect.width, rect.height
        
        audio_sample_array = impulse.getSnapshot(True)
        
        freq = len( audio_sample_array ) / n_cols

        col_width = rect.width/(n_cols +2 )
        row_height = rect.height / (n_rows)
        #print col_width
        for i in range( 0, len( audio_sample_array ), freq ):

            col = i / freq
            rows = int( audio_sample_array[ i ] * n_rows )
            
            cr.set_source_rgba( bar_color[ 0 ], bar_color[ 1 ], bar_color[ 2 ], bar_color[ 3 ] )

            if rows > peak_heights[ i ]:
                peak_heights[ i ] = rows
                peak_acceleration[ i ] = 0.0
            else:
                peak_acceleration[ i ] += .1
                peak_heights[ i ] -= peak_acceleration[ i ]

            if peak_heights[ i ] < 0:
                peak_heights[ i ] = 0

            for row in range( 0, rows ):

                cr.rectangle(
                    col * ( col_width + col_spacing ),
                    rect.height - row * ( row_height + row_spacing ),
                    col_width, -row_height
                )

            cr.fill( )

            cr.set_source_rgba( peak_color[ 0 ], peak_color[ 1 ], peak_color[ 2 ], peak_color[ 3 ] )

            cr.rectangle(
                col * ( col_width + col_spacing ),
                rect.height - peak_heights[ i ] * ( row_height + row_spacing ),
                col_width, -row_height
            )

            cr.fill( )

        cr.fill( )
        cr.stroke( )


if __name__ == "__main__":
    pstl = PystolGTK()
    pstl.window.show()
    gtk.main()
    
