import impulse
import time
import array
import client_wrapper

mapFrequ = {  0   : [0], 
            150   : [1], 
            250   : [2], 
             25   : [6], 
            125   : [7], 
            225   : [8]}

class SoundToLight ():
    def __init__ ( self, universe=1, fade=True, scale=True, fadeStep=0):
        self.universe = universe
        self.bars = 10
        self.fade = fade
        self.scale = scale
        self.fadeStep = fadeStep
        
        self.olddata = []
        self.data = [ 0 for i in range( 256 ) ]
        
        self.manager = FrequencyManager(fade, scale, fadeStep)
        
        print "Frequencys:"
        for freq in range(0, 256, 256/(self.bars)):
                print freq,
        print "."
        
        #init wrapper
        self.wrapper = client_wrapper.ClientWrapper()
        self.client = self.wrapper.Client()
    
    def update(self, audio_sample_array=None):
        if audio_sample_array is None:
            print "Standalone Modus:"
            audio_sample_array = impulse.getSnapshot(True)
        
        l = len(audio_sample_array)
        
        for freq in range(0, l, l/self.bars):
            value = int(audio_sample_array[freq]*100)
            
            channels = self.manager.getChannelList(freq)
            #print freq, ":", channels
            for chan in channels:
                newval = self.manager.getValue(freq, value, self.data[chan])
                
                #print freq, chan, oldval, newval, '\t|\t',
                self.data[chan] = newval
        
        dataArray = array.array('B', self.data)
        self.client.SendDmx(self.universe, dataArray)
            
    def run(self, interval=0.2):
        self._quit = False
        
        while not self._quit:
            self.update()
            time.sleep(interval)
        self.wrapper.Stop()


class FrequencyManager():
    def __init__ (self, scale=False, fade=False, fadeStep=1):
        self.mapping = {}
        self.scale = scale
        self.fade = fade
        self.scaling= {}
        self.defaultScaling = {5: 0, 10: 50, 20: 100, 30: 150}
        self.fadeStep = fadeStep
        
        for f, ch in mapFrequ.iteritems(): 
            self.add(f, ch);
        
    def clear(self):
        self.mapping.clear()
        
    def add(self, freqstep, channels, scale=None):
        if not scale: scale = self.defaultScaling
        self.mapping[freqstep] = channels
        self.scaling[freqstep] = scale
        
    def getChannelList(self, freqstep):
        if freqstep in self.mapping:
            return self.mapping[freqstep]
        else:
            return []           #return empty list

    def getValue(self, freqstep, value, oldval):
        newval = 0
        #print freqstep, value, oldval, 
        
        if self.scale:
            #
            scaleKeys = self.scaling[freqstep].keys()
            scaleKeys.sort()
            
            if value > max(scaleKeys):
                newval = 255
            else:
                for key in scaleKeys:
                    if value <= key:
                        #print value, '<=', key, "==>",self.scaling[freqstep][key]
                        newval = self.scaling[freqstep][key]
                        break
        else:
            newval = int(value*2.5)
        #print "newval is %s for freqstep %s" % (newval, freqstep) 
        
        if self.fade:
            if oldval!=0 and newval<oldval and oldval > self.fadeStep:
                newval = int(oldval-self.fadeStep)
        
        #print newval
                
        return newval
            
#Start:


if __name__ == "__main__":
    stl = SoundToLight()
    stl.run()
