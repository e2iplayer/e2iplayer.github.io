# -*- coding: utf-8 -*-
#

def enum(**enums):
    return type('Enum', (), enums)

# Posible args and values for strwithmeta used for url:

# If meta data exists the at least "iptv_proto" MUST by added to them
#   "iptv_proto":           "m3u8" | "f4m" | "rtmp" | "https" | "http" | "rtsp"
#   "iptv_format":          "mp4" | "ts" | "flv" | "wmv" 
#   "iptv_urlwithlimit":    True | False
#   "iptv_livestream":      True | False
#   "iptv_bitrate":         number
#   "iptv_chank_url":       "http... link"
#   "iptv_block_exteplayer" True | False - default False 
#   "iptv_audio_url"        "http... link"

# Force buffering settings, generally this field should 
# be used only to materials that we know that they do 
# not work without buffering, or vice versa
#   "iptv_buffering":       "required" | "forbidden" 

#   "Host": http header field
#   "User-Agent": http header field
#   "Referer": http header field
#   "Cookie": http header field
#   "Accept": http header field
#   "Range": http header field
class strwithmeta(str):
    def __new__(cls,value,meta={}):
        obj = str.__new__(cls, value)
        obj.meta = {}
        if isinstance(value, strwithmeta):
            obj.meta = value.meta
        else:
            obj.meta = {}
        obj.meta.update(meta)
        return obj
