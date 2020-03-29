#!/usr/bin/env python

import rospy
from std_msgs.msg import *

def remove_substrings(target,substrings):
    result = target[:]
    for s in substrings:
        result = result.replace(s, "")
    return result

# find all variables in an expression
def find_vars(s):
    filtered = remove_substrings(s, ["and","or","not","(",")"])
    result = " ".join(filtered.split()).split(" ")
    return result
'''
    recursively replace all non-inputs variables with their mapping until
    only input variables are left
'''
def make_atomic(expression, inputs, mappings, max_iterations = 10):

    if max_iterations <= 0:
        raise RuntimeError("Reached max variable resolver depth of 10!")
        exit()

    # get list of atoms without duplicates
    non_input_vars = [x for x in list(dict.fromkeys(find_vars(expression))) if x not in inputs]
    # check if replacement still needed
    if len(non_input_vars) <= 0:
        return expression, [x for x in list(dict.fromkeys(find_vars(expression))) if x in inputs]
    # replace
    expression_new = ""
    for var in non_input_vars:
        expression_new = expression.replace("{}".format(var), "({})".format(mappings[var]))
    # next iteration
    return make_atomic(expression_new, inputs, mappings, max_iterations=max_iterations-1)

class BoolFilterNode:
    def __init__(self, verbose=False):
        self.in_out_influence = {}
        self.publishers = {}
        self.subscribers = {}
        self.out_types = {}
        self.mappings = {}
        self.output_funcs = {}
        self.in_values = {}
        self.verbose = verbose

    # Add an input from some topic
    def add_input(self, key, topic_name, topic_type=Bool):
        # make sure input is not there yet
        if key not in self.subscribers:
            # init values for this input
            self.in_values[key] = False if topic_type is Bool else 0
            self.in_out_influence[key] = []
            # create a callback to update respective outputs that use this input
            def callback(data, key=key, topic=topic_name):
                self.in_values[key] = data.data
                if self.verbose:
                    print("inputs = {}".format(self.in_values))
                for out_key in self.in_out_influence[key]:
                    out_type = self.out_types[out_key]
                    res = eval(self.output_funcs[out_key], None, self.in_values)
                    res = bool(res) if out_type is Bool else int(res)
                    if self.verbose:
                        print("--> {} = {} = {}".format(out_key, res, self.mappings[out_key]))
                        print("---> {} type is {}".format(out_key,str(out_type)))
                    msg = out_type(data=res)
                    print(msg)
                    self.publishers[out_key].publish(msg)
            # register the new input (subscribe to the topic)
            self.subscribers[key] = rospy.Subscriber(topic_name, topic_type, callback)
    
    # add a new mapping if it is not present already
    def add_mapping(self, key, mapping):
        if key not in self.mappings:
            self.mappings[key] = mapping

    # assign a variable for which a mapping exists as an output to some topic
    def make_output(self, key, topic_name, topic_type=Bool):
        if key not in self.publishers and key in self.mappings:
            # retrieve the basic mapping
            expression = self.mappings[key]
            # replace all non-inputs 
            expression, inputs = make_atomic(expression, self.subscribers, self.mappings)
            if self.verbose:
                rospy.loginfo("{} := {} ({})".format(key, expression, str(topic_type)))
            # compile user code so we dont need to load anything when getting new inputs
            self.output_funcs[key] = compile(expression, "Expr<{}>".format(key), 'eval')
            self.out_types[key] = topic_type
            # create publisher for output
            self.publishers[key] = rospy.Publisher(topic_name, topic_type, queue_size=5)
            # take note for which inputs this output has to update
            for atom in inputs:
                if key not in self.in_out_influence[atom]:
                    self.in_out_influence[atom].append(key)
        else:
            rospy.logerror("{} already an output or no mapping available!".format(key))

if __name__ == "__main__":
    rospy.init_node("bool_filter_node")

    logic_map = rospy.get_param("~map")
    in_symbols = rospy.get_param("~in")
    out_symbols = rospy.get_param("~out")

    bool_filter = BoolFilterNode(verbose=False)

    for key, value in in_symbols.items():
        v = value.split(",")
        topic_name = v[0].strip()
        topic_type = v[1].strip() if len(v) > 1 else "Bool"
        bool_filter.add_input(key, topic_name, eval(topic_type))

    for key, value in logic_map.items():
        bool_filter.add_mapping(key, mapping = value)

    for key, value in out_symbols.items():
        v = value.split(",")
        topic_name = v[0].strip()
        topic_type = v[1].strip() if len(v) > 1 else "Bool"
        bool_filter.make_output(key, topic_name, eval(topic_type))

    rospy.spin()
