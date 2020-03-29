# Boolean Topic Filters
Want to combine multiple signals into one using boolean logic? This package allows you to do exactly that.

## Supported Operations
- and
- or
- not

## Demo
Simply define inputs, outputs as well as mappings. Mappings also support simple variable replacement:
```
<node pkg="boolean_topic_filters" type="bool_filters.py" name="bool_filter_node">
    <rosparam param="in">
        A : topic_A, Int32
        B : topic_B, Bool
    </rosparam>
    <rosparam param="out">
        C : topic_C, Int64
        D : topic_D, Bool
        E : topic_F, Bool
    </rosparam>
    <rosparam param="map">
        C : not B
        D : A
        E : F or B
        F : not A
    </rosparam>
</node>
```
