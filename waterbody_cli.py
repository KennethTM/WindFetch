#!/usr/bin/env python3

'''
Command line tool for calculating wind fetch
'''

def main():
    import waterbody as wb
    import argparse
    import os 

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help = "Path to input file", 
                        required = True, type = os.path.abspath)
    parser.add_argument("-o", "--output", help = "Path to output file", 
                        required = True, type = os.path.abspath)
    parser.add_argument("-id", "--water_id", help = "Value identifying water", 
                        required = True)
    parser.add_argument("-d", "--directions", help = "Directions to calculate fetch", 
                        required = True)
    parser.add_argument("-w", "--weights", help = "Optional weights for fetch", 
                        required = False)
    parser.add_argument("-s", "--stats", help = "Optional cell stats for fetch", 
                        required = False)

    args = parser.parse_args()

    filein = args.input
    fileout = args.output
    water_id = float(args.water_id)
    directions = [float(i) for i in args.directions.split(",")]

    if args.weights:
        weights = [float(i) for i in args.weights.split(",")]
    else:
        weights = [1]*len(directions)

    if args.stats:
        stats = [str(i) for i in args.stats.split(",")]
    else:
        stats = []

    print("Reading file from " + filein)
    lake = wb.read_waterbody(filein, water_id)

    print("Calcuting fetch for " + str(len(directions)) + " directions")
    out = lake.fetch(directions, weights)

    if stats:
        print("Calculating statistics: " + ", ".join(stats))
        out = out.summary(stats)
    
    print("Saving results to" + fileout)
    wb.save_waterbody(out, fileout)

if __name__ == "__main__":
    main()