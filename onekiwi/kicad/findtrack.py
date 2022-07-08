import pcbnew
from typing import List

from .stackup import *

ANY_LAYER = 'Any'

class TrackTemp:
    def __init__(self, index, types, layer, via1, point, check):
        self.index = index
        self.type = types
        self.check = check
        self.temp_layer = layer
        self.via_layer1 = via1
        self.via_layer2 = None
        self.temp_point = point

class TrackFind:
    def __init__(self, point, layer):
        self.current_point = point
        self.current_layer = layer
        self.status = 'none'
        self.via_index = None
        self.is_via = False
        self.total_length = 0.0
        self.track_length = 0.0
        self.via_length = 0.0
        self.via_count = 0.0
        self.temps:List[TrackTemp] = []

class TrackData:
    def __init__(self, index):
        self.index = index
        self.size = index
        self.items:List[TrackFind] = []

class TrackInfo:
    def __init__(self, status, total_length, track_length, via_length, via_count, tracks):
        self.status = status
        self.total_length = total_length
        self.track_length = track_length
        self.via_length = via_length
        self.via_count = via_count
        self.tracks:List[pcbnew.PCB_TRACK] = tracks

class FindNet:
    def __init__(self, tracks, point_start, point_end, layer_start, layer_end, thickness):
        self.status = 'run'
        self.tracks:List[pcbnew.PCB_TRACK] = []
        self.point_end = point_end
        self.layer_end = layer_end
        self.data:TrackData = TrackData(0)
        self.data.items.append(TrackFind(None, None))
        self.find:TrackFind = TrackFind(point_start, layer_start)
        self.tracks = tracks.copy()
        self.thickness = thickness
        self.info:TrackInfo = TrackInfo('error', 0.0, 0.0, 0.0, 0, [])

    def find_track(self):
        self.find.temps.clear()
        current_point = self.find.current_point
        current_layer = self.find.current_layer
        for index, track in enumerate(self.tracks):
            if track.GetClass() == 'PCB_VIA':
                via_point = track.GetPosition()
                if current_point == via_point:
                    index_data = self.data.index
                    check_data = self.data.items[index_data].temps[index].check
                    if check_data == 0:
                        self.find.temps.append(TrackTemp(index, 'via',  ANY_LAYER, current_layer, via_point, 1))
            else:
                track_start = track.GetStart()
                track_end = track.GetEnd()
                track_layer = track.GetLayer()
                if current_point == track_start and (current_layer == track_layer or current_layer == ANY_LAYER):
                    index_data = self.data.index
                    check_data = self.data.items[index_data].temps[index].check
                    if check_data == 0:
                        self.find.temps.append(TrackTemp(index, 'track',  track_layer, None, track_end, 1))
                    
                elif current_point == track_end and (current_layer == track_layer or current_layer == ANY_LAYER):
                    index_data = self.data.index
                    check_data = self.data.items[index_data].temps[index].check
                    if check_data == 0:
                        self.find.temps.append(TrackTemp(index, 'track',  track_layer, None, track_start, 1))
    
    def find_track_round(self):
        self.find.temps.clear()
        current_point = self.find.current_point
        current_layer = self.find.current_layer
        xc = round(current_point.x/1000000, 4)
        yc = round(current_point.y/1000000, 4)
        for index, track in enumerate(self.tracks):
            if track.GetClass() == 'PCB_VIA':
                via_point = track.GetPosition()
                xv = round(via_point.x/1000000, 4)
                yv = round(via_point.y/1000000, 4)
                if xc == xv and yc == yv:
                    index_data = self.data.index
                    check_data = self.data.items[index_data].temps[index].check
                    if check_data == 0:
                        self.find.temps.append(TrackTemp(index, 'via',  ANY_LAYER, current_layer, via_point, 1))
            else:
                track_start = track.GetStart()
                track_end = track.GetEnd()
                track_layer = track.GetLayer()
                xs = round(track_start.x/1000000, 4)
                ys = round(track_start.y/1000000, 4)
                xe = round(track_end.x/1000000, 4)
                ye = round(track_end.y/1000000, 4)
                
                if xc == xs and yc == ys and (current_layer == track_layer or current_layer == ANY_LAYER):
                    index_data = self.data.index
                    check_data = self.data.items[index_data].temps[index].check
                    if check_data == 0:
                        self.find.temps.append(TrackTemp(index, 'track',  track_layer, None, track_end, 1))
                    
                elif xc == xe and yc == ye and (current_layer == track_layer or current_layer == ANY_LAYER):
                    index_data = self.data.index
                    check_data = self.data.items[index_data].temps[index].check
                    if check_data == 0:
                        self.find.temps.append(TrackTemp(index, 'track',  track_layer, None, track_start, 1))

    def check_add_track(self):
        index_data = self.data.index
        for i in range(1, len(self.find.temps)):
            self.data.size += 1
            # copy
            current = self.data.items[index_data].temps
            self.data.items.append(TrackFind(None, None))
            self.data.items[self.data.size].temps = current.copy()
            
            #debug
            """
            count = len(self.data.items)
            xx = len(self.data.items[0].temps)
            print('=========')
            for index in range(xx):
                a = []
                for ii in range(count):
                    a.append(self.data.items[ii].temps[index].check)
                print('%d. %s' %(index, a))
            """

            # add
            find = self.find.temps[i]
            index = find.index
            self.data.items[self.data.size].temps[index] = find
            self.data.items[self.data.size].current_layer = find.temp_layer
            self.data.items[self.data.size].current_point = find.temp_point

            if self.find.is_via == True:
                ind = self.find.via_index
                self.data.items[self.data.size].temps[ind].via_layer2 = find.temp_layer
        
        temp_find = self.find.temps[0]
        index = temp_find.index
        self.find.current_point = temp_find.temp_point
        self.find.current_layer = temp_find.temp_layer
        index_data = self.data.index
        self.data.items[index_data].temps[index] = temp_find
        if self.find.is_via == True:
                ind = self.find.via_index
                self.data.items[index_data].temps[ind].via_layer2 = temp_find.temp_layer
                self.find.is_via = False

    def check_add_via1(self):
        temp_find = self.find.temps[0]
        index = temp_find.index
        self.find.via_index = index
        self.find.is_via = True
        self.find.current_point = temp_find.temp_point
        self.find.current_layer = temp_find.temp_layer
        index_data = self.data.index
        self.data.items[index_data].temps[index] = temp_find
        
    def check_track(self):
        track_find = 0
        via_find = 0
        for item in self.find.temps:
            if item.check == 1 and item.type == 'track':
                track_find += 1
            if item.check == 1 and item.type == 'via':
                via_find += 1
        if track_find == 0 and via_find == 0:
            if self.status == 'run':
                self.status = 'round'
                self.find_track_round()
                self.check_track()
            else:
                self.status = 'error'
        elif track_find > 0 and via_find == 0:
            self.status = 'run'
            self.check_add_track()
        elif track_find == 0 and via_find == 1:
            self.status = 'run'
            self.check_add_via1()
        elif track_find > 0 and via_find == 1:
            self.status = 'unkown'
        elif via_find > 1:
            self.status = 'unkown'

        if self.point_end == self.find.current_point and self.layer_end == self.find.current_layer:
            self.status = 'done'

    def find_next_track(self):
        self.find_track()
        self.check_track()
        if self.status == 'run':
            self.find_next_track()
        else:
            self.data.items[self.data.index].status = self.status
            if self.data.index < self.data.size:
                self.data.index += 1
                self.find.current_layer = self.data.items[self.data.index].current_layer
                self.find.current_point = self.data.items[self.data.index].current_point

                self.find_next_track()

    def get_via_length(self, layer1, layer2):
        stackup = []
        via_length = 0.0
        if layer1 == None or layer2 == None:
            via_length = 0.0
        else:
            if layer1 > layer2:
                temp_layer = layer1
                layer1 = layer2
                layer2 = temp_layer
            start = 2*layer1
            end = 2*layer2
            if end >= len(self.thickness):
                end = len(self.thickness)
                stackup = self.thickness[start:]
            else:
                stackup = self.thickness[start:end+1]
            offset = 0.0
            offset = (stackup[0] + stackup[len(stackup) - 1])/2
            via_length = 0.0
            for item in stackup:
                via_length += item
            via_length = via_length - offset
        return via_length

    def get_length(self):
        for i, nettrack in enumerate(self.data.items):
            sum_track_length = 0.0
            sum_via_length = 0.0
            via_count = 0
            for index, track in enumerate(nettrack.temps):
                if track.check == 1 and track.type == 'track':
                    tr = self.tracks[index].GetLength()
                    sum_track_length += tr
                if track.check == 1 and track.type == 'via':
                    via_count += 1
                    layer1 = self.data.items[i].temps[index].via_layer1
                    layer2 = self.data.items[i].temps[index].via_layer2
                    via_length = self.get_via_length(layer1, layer2)
                    sum_via_length += via_length
            #sum_track_length = round(sum_track_length/pcbnew.IU_PER_MM, 4)
            self.data.items[i].track_length = sum_track_length/pcbnew.IU_PER_MM
            self.data.items[i].via_length = sum_via_length
            self.data.items[i].via_count = via_count
            self.data.items[i].total_length = (sum_track_length/pcbnew.IU_PER_MM) + sum_via_length

    def find_min_track(self):
        check = False
        index = 0
        min_length = 0.0
        for i, item in enumerate(self.data.items):
            if item.status == 'done':
                if check == False:
                    check = True
                    min_length = item.total_length
                    index = i
                else:
                    if min_length > item.total_length:
                        min_length = item.total_length
                        index = i
        if check == True:
            total_length = self.data.items[index].total_length
            track_length = self.data.items[index].track_length
            via_length = self.data.items[index].via_length
            via_count = self.data.items[index].via_count
            tracks = []
            for i, track in enumerate(self.tracks):
                if self.data.items[index].temps[i].check == 1:
                    tracks.append(track)
            info = TrackInfo('done', total_length, track_length, via_length, via_count, tracks)
            self.info = info

    def get_min_track(self):
        count = len(self.tracks)
        temp = [TrackTemp(None, None, None, None, None, 0)] * count
        index_data = self.data.index
        self.data.items[index_data].temps = temp.copy()

        self.find_next_track()
        self.get_length()
        self.find_min_track()
        return self.info
        