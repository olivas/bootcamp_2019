#!/usr/bin/env python

import logging

class I3Service(object):
    pass

class I3FrameObject(object):
    pass

class I3Frame(object):
    def __init__(self, frame_type='P'):
        self.frame_type = frame_type
        self.state = dict()

    def __getitem__(self, key):
        return self.state[key]
        
    def __setitem__(self, key, value):
        if isinstance(value, I3FrameObject):
            self.state[key] = value
        else:
            raise TypeError("%s is not an I3FrameObject" % key)

    def __str__(self):
        result = '[ I3Frame (%s) \n' % self.frame_type
        result += "".join(['  %s: %s' % (k,v) for k,v in self.state.items()])
        result += '\n]'
        return result
        
class I3Module(object):
    '''
    Base class for IceTray modules.
    '''
    def __init__(self, context):
        self.context = context

    def Configure(self):
        pass
        
    def GenerateFrame(self):
        '''
        This is only called if it's first in the list.
        It's the job of the 'Driving Module' to create frames.
        '''
        raise NotImplementedError
        
    def Geometry(self, frame):
        return True
        
    def Calibration(self, frame):
        return True
        
    def DetectorStatus(self, frame):
        return True
        
    def DAQ(self, frame):
        return True
        
    def Physics(self, frame):
        return True

    def Default(self, frame):
        return True

class I3Tray(object):
    def __init__(self):
        self.context = dict()
        self.__modules = list()

    def Add(self, obj, name, **kwargs):
        '''
        Adds I3Modules and I3Services to the framework.
        '''
        self.__add(obj, name, **kwargs)

    def Execute(self):
        '''
        Configures the modules and then executes them.
        in the order they were added.
        '''
        self.__execute()
        
    def __add(self, obj, name, **kwargs):
        
        if issubclass(obj, I3Service):
            self.context[name] = obj(**kwargs)
        elif issubclass(obj, I3Module):
            self.__modules.append(obj(self.context, **kwargs))
        elif callable(obj):
            # support only function objects for now
            print(kwargs)
            self.__modules.append(obj(self.context, **kwargs))
        else:
            raise TypeError(": %s" % name)

    def __execute(self):

        for module in self.__modules:
            if hasattr(module, 'Configure'):
                module.Configure()
        
        while True:
            frame = self.__modules[0].GenerateFrame()
            if not frame:
                break
            
            for module in self.__modules:
                if callable(module):
                    if not module(frame):
                        continue
                elif frame.frame_type == 'G':
                    if not module.Geometry(frame):
                        continue
                elif frame.frame_type == 'C':
                    if not module.Calibration(frame):
                        continue
                elif frame.frame_type == 'D':
                    if not module.DetectorStatus(frame):
                        continue
                elif frame.frame_type == 'Q':
                    if not module.DAQ(frame):
                        continue
                elif frame.frame_type == 'P':
                    if not module.Physics(frame):
                        continue
                else:
                    if not module.Default(frame):
                        continue

########
#Example
########
import pickle
                
class I3Reader(I3Module):
    def __init__(self, context, filename):
        super(I3Reader, self).__init__(context)
        self.frames = pickle.load(open(filename))
        self.frame_counter = 0
        
    def GenerateFrame(self):
        try:
            f = self.frames[self.frame_counter]
        except IndexError:
            return
        
        self.frame_counter += 1        
        frame = I3Frame(f['type'])
        frame.state = f['state']
        return frame
    
class I3Source(I3Module):
    def __init__(self, context, n_frames, frame_type):
        super(I3Source, self).__init__(context)
        self.n_frames = n_frames
        self.frame_type = frame_type
        self.n_frames_served = 0
        
    def GenerateFrame(self):
        if self.n_frames_served < self.n_frames:
            self.n_frames_served += 1
            return I3Frame(self.frame_type)

class Dump:
    def __init__(self, context):
        self.context = context
        self.frame_counter = 0
        
    def __call__(self, frame):
        self.frame_counter += 1
        print("Frame Counter = %d" % self.frame_counter)
        print(frame)

class I3Writer:
    def __init__(self, context, filename):
        self.context = context
        self.filename = filename
        
    def __call__(self, frame):
        with open(self.filename, 'w') as f:
            pickle.dump({'type' : frame.frame_type,
                         'state' : frame.state},
                        f)
        
if __name__ == '__main__':
        
    tray = I3Tray()
    tray.Add(I3Source,'source', n_frames=100, frame_type='Q') # serves up 100 DAQ frames
    tray.Add(Dump, 'dump')
    tray.Add(I3Writer, 'writer', filename='output.pkl')
    tray.Execute()




            
