#@ DatasetService ds
#@ DisplayService display
#@ DatasetIOService dsio
#@ ConvertService cs
#@ OpService op
#@ SNTService snt

"""
file: Fill_Demo.py
version: 20211012
info: Demonstrates how to fill programatically
"""

from ij import IJ, ImagePlus
from ij.plugin import LutLoader
from net.imagej import Dataset
from net.imglib2.img.display.imagej import ImageJFunctions
from net.imglib2.type.logic import BitType
from net.imglib2.type.numeric.real import FloatType
from net.imglib2.type.numeric.integer import UnsignedByteType
from sc.fiji.snt import Tree, FillConverter
from sc.fiji.snt.tracing import FillerThread
from sc.fiji.snt.tracing.cost import Reciprocal
from sc.fiji.snt.util import ImgUtils

# Documentation Resources: https://imagej.net/SNT:_Scripting
# Latest SNT API: https://morphonets.github.io/SNT/

from java.io import File
import os

def processFolder(input, output, suffix):
	for root, dirs, files in os.walk(input):
		for filename in files:
			fullpath = os.path.join(root, filename)
			traces_filename = filename.replace('.nd2', '.traces')
			# print(path)
			if filename.endswith(suffix) and (traces_filename in files or "SNT_Data.traces" in files):
				fulltraces = os.path.join(root, traces_filename if traces_filename in files else "SNT_Data.traces")
				processFile(root, output, filename, fullpath, traces_filename, fulltraces)

def processFile(input, output, filename, fullpath, trace_filename, fulltraces):
	imp = IJ.openImage(fullpath)
	IJ.run(imp, "Bio-Formats", "open=[" + fullpath +"] autoscale color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT")
	# IJ.run("Brightness/Contrast...")
	IJ.run(imp, "Enhance Contrast", "saturated=0.35")
	IJ.run(imp, "Enhance Contrast", "saturated=0.35")
	IJ.run(imp, "Enhance Contrast", "saturated=0.35")
	IJ.run(imp, "Enhance Contrast", "saturated=0.35")
	# setMinAndMax(122, 226);
	IJ.run(imp, "Apply LUT", "stack")
	IJ.saveAs(imp, "Tiff", output + filename)
    
	traces = Tree(fulltraces)
	dataset = cs.convert(imp, Dataset)
	print(dataset)
	
	traces.assignImage(dataset)
	
	# Compute min-max and create cost function
	
	min_max = op.stats().minMax(dataset)
	cost = Reciprocal(min_max.getA().getRealDouble(), min_max.getB().getRealDouble())
	
	threshold = 0.01
	fillers = []
	for trace in traces.list():
		filler = FillerThread(dataset, threshold, cost)
		filler.setSourcePaths([trace])
		filler.setStopAtThreshold(True)
		filler.setStoreExtraNodes(False)
		filler.run()
		fillers.append(filler)
	    
	converter = FillConverter(fillers)
	showBinaryMask(dataset, converter)
	IJ.saveAs("tiff", output + filename)
	IJ.run("Close")
	IJ.run("Close")
    

def copyAxes(dataset, out_dataset):
	# Copy scale and axis metadata to the output.
	# There's probably a better way to do this...
	for d in range(dataset.numDimensions()):
		out_dataset.setAxis(dataset.axis(d), d)

def showBinaryMask(dataset, converter):
	output = op.create().img(dataset, BitType())
	converter.convertBinary(output)
	output = ds.create(output)
	copyAxes(dataset, output)
	display.createDisplay("Binary Fill Mask", output)


input = "Z:/Ophthalmology/Research/SchwartzLab/Maribel/Vincent/MEA_Brain_Slices/raw"
output = "Z:/Ophthalmology/Research/SchwartzLab/Maribel/Vincent/MEA_Brain_Slices/processed/masks/"
suffix = ".nd2"

processFolder(input, output, suffix)
print("done")