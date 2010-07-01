from troveclient.Objects import Query
import simplejson

class EncoderFactory:
    _encoders = {}

    def register(self, encoder_class):
        if encoder_class.object_name not in self._encoders:
            self._encoders[encoder_class.object_name] = encoder_class

    def deregister(self, encoder_class):
        if encoder_class.object_name not in self._encoders:
            del self._encoders[encoder_class.object_name]

    def get_encoder_for(self, object):
        name = object.__class__.__name__
        if name in self._encoders:
            return self._encoders[name]
        else:
            return None
        
class DecoderFactory:
    decoders = {}
    

class SomeUsefulJSONUtilities:
    
    def make_it_utc(date_with_no_home):
        from dateutil.tz import tzutc

        if date_with_no_home.tzinfo is None or date_with_no_home.tzinfo=="":
            date_with_no_home = date_with_no_home.replace(tzinfo=tzutc())
        else:
            date_with_no_home = date_with_no_home.astimezone(tzutc())
        
        ##TODO FIXME don't need this hack now? this is using mongo,
        ## need to look at mongo date times
        # this hack is here since MySQL doesn't support timezones in datetime
        date_with_no_home = date_with_no_home.replace(tzinfo=None)  
        return date_with_no_home

    make_it_utc = staticmethod(make_it_utc)

# Now We Register Stuff

encoders = EncoderFactory()

        
class __QueryEncoder(simplejson.JSONEncoder):
    
    object_name = Query().__class__.__name__
    
    def default(self, object):
        
        encoded_list = {}
        encoded_list['services'] = object.services
        encoded_list['tags-optional'] = object.tags_optional
        encoded_list['tags-required'] = object.tags_required
        encoded_list['force-update'] = object.force_update
        if object.date_from is not None:
            object.date_from = SomeUsefulJSONUtilities.make_it_utc(object.date_from)
            encoded_list['date-from'] = object.date_from.strftime("%Y-%m-%d %H:%M:%S %Z")
        if object.date_to is not None:
            object.date_to = SomeUsefulJSONUtilities.make_it_utc(object.date_to)
            encoded_list['date-to'] = object.date_to.strftime("%Y-%m-%d %H:%M:%S %Z")
        encoded_list['attributes'] = object.attributes
        return encoded_list

encoders.register(__QueryEncoder)
