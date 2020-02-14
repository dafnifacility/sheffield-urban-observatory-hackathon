class Converter():
    url = ''
    conversion_dict = {}
    
    def convert_parameter(self, key, value):
        if self.conversion_dict[key][0]:
            new_key = self.conversion_dict[key][0]
        else:
            new_key = key
        if self.conversion_dict[key][1]:
            new_value = self.conversion_dict[key][1](value)
        else:
            new_value = value
        return(new_key, new_value)
    
    def convert_parameters(self, parameters):
        request_url = self.url + '?'

        for key, value in parameters.items():
            if key in self.conversion_dict:
                key, value = self.convert_parameter(key, value)

            to_add = key + '=' + value
            request_url += to_add + '&'
        request_url = request_url[:-1]
        return request_url