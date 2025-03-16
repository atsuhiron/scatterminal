# scatterminal
Draw scatter plot on terminal

## Requirement
- Python >= 3.10

## Installation
```shell
pip install scatterminal
```
After installation, the `plot` command will become available.

## Usage
This tool supports the following two types of data sources:

### 1. CSV files
The following command on the terminal will read a csv file (or tsv file) and plot a scatter plot.
```shell
plot tests/samples/single_column.csv
```
```
  12.000+
        |                                        *  *   *
  11.000+                                     *
  10.000+                                                  *
        |                                  *                  *
v 9.000 +                                                        *
a 8.000 +
l 7.000 +                              *                             *
u       |
e 6.000 +        *                  *
  5.000 +     *     *  *
        |                 *   *  *
  4.000 +----+--------------+---------------+--------------+--------------+
           0.000          5.000          10.000         15.000       20.000


*: value
```
Primarily, this type is designed for use in the terminal.  
However, it can also be executed within a Python script, yielding the same result:
```python
from scatterminal.plot import plot_csv

plot_csv(["tests/samples/single_column.csv"])
```

### 2. `list` objects of Python
This method is only available within Python scripts.

```python
from scatterminal.plot import plot_inline
from scatterminal.data_layer_model import SimpleDataSequence

x_arr = [x - 2 for x in range(8)]
y_arr1 = [x * x/2 - 2 * x for x in x_arr]
y_arr2 = [-x * x/2 + 1 * x + 3 for x in x_arr]
plot_inline(
    [
        SimpleDataSequence(x_arr, y_arr1, "y1"),
        SimpleDataSequence(x_arr, y_arr2, "y2"),
    ]
)
```
```
7.500  +
       |     *
5.000  +
       |                             o
       |             *       o              o                       *
2.500  +             o                              o
       |
0.000  +                     *                              *
       |     o                       *              *       o
-2.500 +                                    *
       |
-5.000 +                                                            o
       |-+-------------------+------------------+-------------------+------
      -2.500               0.000              2.500               5.000


*: y1  o: y2
```

## Detailed specifications
### Data sequences
#### Basic format
The following is an example of the most basic file format that can be plotted.
Each column represents the x-axis and y-axis coordinates of a single data sequence.
```csv:test/samples/double_column.csv
x,y
0.0000,0.0000
0.6283,0.5878
1.2566,0.9511
1.8850,0.9511
2.5133,0.5878
3.1416,0.0000
3.7699,-0.5878
4.3982,-0.9511
5.0265,-0.9511
5.6549,-0.5878
6.2832,-0.0000
6.9115,0.5878
```
#### Simplified format
If there is a single column, the x-axis coordinates are interpreted as omitted.
```csv:tests/samples/single_column.csv
value
5.5
6.0
5.2
5.2
4.8
4.6
4.9
5.7
7.6
9.4
10.4
11.3
11.4
11.3
10.3
9.7
8.4
7.0
```
The omitted x-axis coordinates are implicitly compensated by a sequence of integers beginning with zero.  
Thus, the above example is equivalent to the following two-column format.
```csv
,value
0,5.5
1,6.0
2,5.2
3,5.2
4,4.8
5,4.6
6,4.9
7,5.7
8,7.6
9,9.4
10,10.4
11,11.3
12,11.4
13,11.3
14,10.3
15,9.7
16,8.4
17,7.0
```
#### Multiple data sequences
When drawing multiple data sequences, multiple files are loaded at the same time.  
In the following example, you will need the coordinates of each of the two sequences (i.e., `x1`, `y1`, `x2`, and `y2`).
```shell
plot tests/samples/single_column.csv tests/samples/single_column_seq2.csv
```
```
       |
       |                                         o  o  o
       |                                     o             o
12.500 +                                  o                   o
       |                                         *  *  *         o
10.000 +                               o     *             *        o
       |                                  *                   *
7.500  +     o  o  o  o             o                            *
       |                  o  o  o      *
       |                                                            *
5.000  +     *  *  *  *             *
       |                  *  *  *
2.500  +----+---------------+--------------+---------------+--------------+
          0.000           5.000         10.000          15.000       20.000


*: value  o: value2
```
Sometimes, however, multiple data sequences share a single x-axis coordinate.  
In this case, it is possible to combine the files into one, with each column representing `x`, `y1`, and `y2`.
```csv:tests/samples/triple_column.csv
x,sin,cos
0.0000,0.0000,1.0000
0.6283,0.5878,0.8090
1.2566,0.9511,0.3090
1.8850,0.9511,-0.3090
2.5133,0.5878,-0.8090
3.1416,0.0000,-1.0000
3.7699,-0.5878,-0.8090
4.3982,-0.9511,-0.3090
5.0265,-0.9511,0.3090
5.6549,-0.5878,0.8090
6.2832,-0.0000,1.0000
6.9115,0.5878,0.8090
```
This is plotted as follows.
```shell
plot tests/samples/triple_column.csv
```
```
       |
1.000  +     o         *    *                                  o
       |          o                                       o         o
       |          *              *                                  *
0.500  +               o                             o
       |
0.000  +     *                        *                        *
       |
-0.500 +                    o                   o
       |                                   *              *
       |                         o         o
-1.000 +                              o         *    *
       |-----+-------------------+-------------------+-------------------+-
           0.000               2.500               5.000              7.500
                                         x

*: sin  o: cos
```

### Logarithm
The `--yscale log` option will give you a logarithmic display.
```shell
plot tests/samples/double_column_power.csv tests/samples/double_column_power_seq2.csv --yscale log
```
```
        |                                                            o
316.228 +                                       *  *              o
        |                                     *              o  o
100.000 +                                   *           o o
        |                      o  o o o  o  o o o  o  o
31.623  +                           *
        |                      *  *
10.000  +                   *
        |                 *
3.162   +            *  *
        |          *
        |       *
1.000   +----+*----------+------------+-----------+-----------+-----------+
           0.000       5.000       10.000      15.000      20.000    25.000


*: power_val  o: power_val2
```