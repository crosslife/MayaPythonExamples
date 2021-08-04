#-
# ==========================================================================
# Copyright (C) 1995 - 2006 Autodesk, Inc. and/or its licensors.  All 
# rights reserved.
#
# The coded instructions, statements, computer programs, and/or related 
# material (collectively the "Data") in these files contain unpublished 
# information proprietary to Autodesk, Inc. ("Autodesk") and/or its 
# licensors, which is protected by U.S. and Canadian federal copyright 
# law and by international treaties.
#
# The Data is provided for use exclusively by You. You have the right 
# to use, modify, and incorporate this Data into other products for 
# purposes authorized by the Autodesk software license agreement, 
# without fee.
#
# The copyright notices in the Software and this entire statement, 
# including the above license grant, this restriction and the 
# following disclaimer, must be included in all copies of the 
# Software, in whole or in part, and all derivative works of 
# the Software, unless such copies or derivative works are solely 
# in the form of machine-executable object code generated by a 
# source language processor.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. 
# AUTODESK DOES NOT MAKE AND HEREBY DISCLAIMS ANY EXPRESS OR IMPLIED 
# WARRANTIES INCLUDING, BUT NOT LIMITED TO, THE WARRANTIES OF 
# NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A PARTICULAR 
# PURPOSE, OR ARISING FROM A COURSE OF DEALING, USAGE, OR 
# TRADE PRACTICE. IN NO EVENT WILL AUTODESK AND/OR ITS LICENSORS 
# BE LIABLE FOR ANY LOST REVENUES, DATA, OR PROFITS, OR SPECIAL, 
# DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES, EVEN IF AUTODESK 
# AND/OR ITS LICENSORS HAS BEEN ADVISED OF THE POSSIBILITY 
# OR PROBABILITY OF SUCH DAMAGES.
#
# ==========================================================================
#+

########################################################################
# DESCRIPTION:
#
# Produces the Python commands "spMoveToolCmd" and "spMoveToolContext".
#
# Interactive tool for moving objects and components. 
#
# This is an example of a selection-action tool. When nothing is selected, this
# tool behaves in exactly the same way as the selection tool in Maya. Once an object
# is selected, the tool turns into a translation tool.
#
# The plug-in can translate: 
#	- transforms 
#	- NURBS curve CVs 
#	- NURBS surface CVs 
#	- polygonal vertices 
#
# This plug-in can only perform translation in orthographic views. 
# Undo, redo, and journalling are supported by this tool.  
#
# To use this plug-in, execute the following:
#
#	import maya
#	maya.cmds.loadPlugin("moveTool.py")
#	maya.cmds.spMoveToolContext("spMoveToolContext1")
#	shelfTopLevel = maya.mel.eval("global string $gShelfTopLevel;$temp = $gShelfTopLevel")
#	maya.cmds.setParent("%s|General" % shelfTopLevel)
#	maya.cmds.toolButton("spMoveTool1", cl="toolCluster", t="spMoveToolContext1", i1="moveTool.xpm") 
#	# Remove UI objects with
#	maya.cmds.deleteUI("spMoveToolContext1")
#	maya.cmds.deleteUI("spMoveTool1")
#
# This creates a new entry in the "Shelf1" tab of the tool shelf called "moveTool". Click the
# new icon, then select an object and drag it around in an orthographic view. The left mouse
# button allows movement in two directions, while the middle mouse button constrains the movement
# to a single direction. 
#
# Note that you must have a Shelf1 tab before executing the commands. 
#
########################################################################

#
#	Creation Date:   2 October 2006
#

import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaUI as OpenMayaUI
import sys, math

kPluginCmdName="spMoveToolCmd"
kPluginCtxName="spMoveToolContext"
kVectorEpsilon = 1.0e-3

# keep track of instances of MoveToolCmd to get around script limitation
# with proxy classes of base pointers that actually point to derived
# classes
kTrackingDictionary = {}

# command
class MoveToolCmd(OpenMayaMPx.MPxToolCommand):
	kDoIt, kUndoIt, kRedoIt = 0, 1, 2

	def __init__(self):
		OpenMayaMPx.MPxToolCommand.__init__(self)
		self.setCommandString(kPluginCmdName)
		self.__delta = OpenMaya.MVector()
		kTrackingDictionary[OpenMayaMPx.asHashable(self)] = self

	def __del__(self):
		del kTrackingDictionary[OpenMayaMPx.asHashable(self)]

	def doIt(self, args):
		argData = OpenMaya.MArgDatabase(self.syntax(), args)
		vector = OpenMaya.MVector(1.0, 0.0, 0.0)
		if args.length() == 1:
			vector.x = args.asDouble(0)
		elif args.length == 2:
			vector.x = args.asDouble(0)
			vector.y = args.asDouble(1)
		elif args.length == 3:
			vector.x = args.asDouble(0)
			vector.y = args.asDouble(1)
			vector.z = args.asDouble(2)
		self.__delta = vector
		self.__action(MoveToolCmd.kDoIt)

	def redoIt(self):
		self.__action(MoveToolCmd.kRedoIt)

	def undoIt(self):
		self.__action(MoveToolCmd.kUndoIt)

	def isUndoable(self):
		return True

	def finalize(self):
		"""
		Command is finished, construct a string for the command
		for journalling.
		"""
		command = OpenMaya.MArgList()
		command.addArg(self.commandString())
		command.addArg(self.__delta.x)
		command.addArg(self.__delta.y)
		command.addArg(self.__delta.z)

		# This call adds the command to the undo queue and sets
		# the journal string for the command.
		#
		try:
			OpenMayaMPx.MPxToolCommand._doFinalize(self, command)
		except:
			pass

	def setVector(self, x, y, z):
		self.__delta.x = x
		self.__delta.y = y
		self.__delta.z = z

	def __action(self, flag):
		"""
		Do the actual work here to move the objects	by vector
		"""
		if flag == MoveToolCmd.kUndoIt:
			vector = -self.__delta
		else:
			vector = self.__delta

		# Create a selection list iterator
		#
		slist = OpenMaya.MSelectionList()
		OpenMaya.MGlobal.getActiveSelectionList(slist)
		sIter = OpenMaya.MItSelectionList(slist)

		mdagPath = OpenMaya.MDagPath()
		mComponent = OpenMaya.MObject()
		spc = OpenMaya.MSpace.kWorld

		# Translate all selected objects
		#
		while not sIter.isDone():
			# Get path and possibly a component
			#
			sIter.getDagPath(mdagPath, mComponent)
			try:
				transFn = OpenMaya.MFnTransform(mdagPath)
			except:
				pass
			else:
				try:
					transFn.translateBy(vector, spc)
				except:
					sys.stderr.write("Error doing translate on transform\n")
				sIter.next()
				continue

			try:
				cvFn = OpenMaya.MItCurveCV(mdagPath, mComponent)
			except:
				pass
			else:
				while not cvFn.isDone():
					cvFn.translateBy(vector, spc)
					cvFn.next()
				cvFn.updateCurve()

			try:
				sCvFn = OpenMaya.MItSurfaceCV(mdagPath, mComponent, True)
			except:
				pass

			else:
				while not sCvFn.isDone():
					while not CvFn.isRowDone():
						sCvFn.translateBy(vector, spc)
						sCvFn.next()
					sCvFn.nextRow()
				sCvFn.updateSurface()

			try:
				vtxFn = OpenMaya.MItMeshVertex(mdagPath, mComponent)
			except:
				pass
			else:
				while not vtxFn.isDone():
					vtxFn.translateBy(vector, spc)
					vtxFn.next()
				vtxFn.updateSurface()

			sIter.next()


class MoveContext(OpenMayaMPx.MPxSelectionContext):
	kTop, kFront, kSide, kPersp = 0, 1, 2, 3
	
	def __init__(self):
		OpenMayaMPx.MPxSelectionContext.__init__(self)
		self._setTitleString("moveTool")
		self.setImage("moveTool.xpm", OpenMayaMPx.MPxContext.kImage1)
		self.__currWin = 0
		self.__view = OpenMayaUI.M3dView()
		self.__startPos_x = 0
		self.__endPos_x = 0
		self.__startPos_y = 0
		self.__endPos_y = 0
		self.__cmd = None

	def toolOnSetup(self, event):
		self._setHelpString("drag to move selected object")

	def doPress(self, event):
		OpenMayaMPx.MPxSelectionContext.doPress(self, event)
		spc = OpenMaya.MSpace.kWorld
		
		# If we are not in selecting mode (i.e. an object has been selected)
		# then set up for the translation.
		#
		if not self._isSelecting():
			argX = OpenMaya.MScriptUtil(0)
			argXPtr = argX.asShortPtr()
			argY = OpenMaya.MScriptUtil(0)
			argYPtr = argY.asShortPtr()
			event.getPosition(argXPtr, argYPtr)
			self.__startPos_x = argX.getShort(argXPtr)
			self.__startPos_y = argY.getShort(argYPtr)
			self.__view = OpenMayaUI.M3dView.active3dView()

			camera = OpenMaya.MDagPath()
			self.__view.getCamera(camera)
			fnCamera = OpenMaya.MFnCamera(camera)
			upDir = fnCamera.upDirection(spc)
			rightDir = fnCamera.rightDirection(spc)

			# Determine the camera used in the current view
			#
			if fnCamera.isOrtho():
				if upDir.isEquivalent(OpenMaya.MVector.zNegAxis, kVectorEpsilon):
					self.__currWin = MoveContext.kTop
				elif rightDir.isEquivalent(OpenMaya.MVector.xAxis, kVectorEpsilon):
					self.__currWin = MoveContext.kFront
				else:
					self.__currWin = MoveContext.kSide
			else:
				OpenMaya.MGlobal.displayWarning('moveTool only works in top, front and side views')
				self.__currWin = MoveContext.kPersp

			# Create an instance of the move tool command.
			#
			newCmd = self._newToolCommand()
			self.__cmd = kTrackingDictionary.get(OpenMayaMPx.asHashable(newCmd), None)
			self.__cmd.setVector(0.0, 0.0, 0.0)

	def doDrag(self, event):
		OpenMayaMPx.MPxSelectionContext.doDrag(self, event)

		# If we are not in selecting mode (i.e. an object has been selected)
		# then do the translation.
		#

		if not self._isSelecting():
			argX = OpenMaya.MScriptUtil(0)
			argXPtr = argX.asShortPtr()
			argY = OpenMaya.MScriptUtil(0)
			argYPtr = argY.asShortPtr()
			event.getPosition(argXPtr, argYPtr)
			self.__endPos_x = argX.getShort(argXPtr)
			self.__endPos_y = argY.getShort(argYPtr)

			startW = OpenMaya.MPoint()
			endW = OpenMaya.MPoint()
			vec = OpenMaya.MVector()
			self.__view.viewToWorld(self.__startPos_x, self.__startPos_y, startW, vec)
			self.__view.viewToWorld(self.__endPos_x, self.__endPos_y, endW, vec)
			downButton = event.mouseButton()

			# We reset the the move vector each time a drag event occurs
			# and then recalculate it based on the start position.
			#
			self.__cmd.undoIt()
			if self.__currWin == MoveContext.kTop:
				if downButton == OpenMayaUI.MEvent.kMiddleMouse:
					self.__cmd.setVector(endW.x - startW.x, 0.0, 0.0)
				else:
					self.__cmd.setVector(endW.x - startW.x, 0.0, endW.z - startW.z)

			elif self.__currWin == MoveContext.kFront:
				if downButton == OpenMayaUI.MEvent.kMiddleMouse:

					self.__cmd.setVector(endW.x - startW.x, 0.0, 0.0)

				else:

					self.__cmd.setVector(endW.x - startW.x, endW.y - startW.y, 0.0)

			elif self.__currWin == MoveContext.kSide:
				if downButton == OpenMayaUI.MEvent.kMiddleMouse:
					self.__cmd.setVector(0.0, 0.0, endW.z - startW.z)
				else:
					self.__cmd.setVector(0.0, endW.y - startW.y, endW.z - startW.z)

			self.__cmd.redoIt()
			self.__view.refresh(True)

	def doRelease(self, event):
		OpenMayaMPx.MPxSelectionContext.doRelease(self, event)
		if not self._isSelecting():
			argX = OpenMaya.MScriptUtil(0)
			argXPtr = argX.asShortPtr()
			argY = OpenMaya.MScriptUtil(0)
			argYPtr = argY.asShortPtr()
			event.getPosition(argXPtr, argYPtr)
			self.__endPos_x = argX.getShort(argXPtr)
			self.__endPos_y = argY.getShort(argYPtr)

			# Delete the move command if we have moved less then 2 pixels
			# otherwise call finalize to set up the journal and add the
			# command to the undo queue.

			#
			if (math.fabs(self.__startPos_x - self.__endPos_x) < 2 and 
					math.fabs(self.__startPos_y - self.__endPos_y) < 2):
				self.__cmd = None
				self.__view.refresh(True)
			else:
				self.__cmd.finalize()
				self.__view.refresh(True)

	def doEnterRegion(self, event):
		"""
		Print the tool description in the help line.
		"""
		self._setHelpString("click on object and drag to move it")


#############################################################################


class MoveContextCommand(OpenMayaMPx.MPxContextCommand):
	def __init__(self):
		OpenMayaMPx.MPxContextCommand.__init__(self)

	def makeObj(self):
		return OpenMayaMPx.asMPxPtr(MoveContext())

def cmdCreator():
	return OpenMayaMPx.asMPxPtr(MoveToolCmd())

def ctxCmdCreator():
	return OpenMayaMPx.asMPxPtr(MoveContextCommand())

def syntaxCreator():
	syntax = OpenMaya.MSyntax()
	syntax.addArg(OpenMaya.MSyntax.kDouble)
	syntax.addArg(OpenMaya.MSyntax.kDouble)
	syntax.addArg(OpenMaya.MSyntax.kDouble)
	return syntax

# Initialize the script plug-in

def initializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject, "Autodesk", "1.0", "Any")
	try:
		mplugin.registerContextCommand(kPluginCtxName, ctxCmdCreator, kPluginCmdName, cmdCreator, syntaxCreator)
	except:
		sys.stderr.write("Failed to register context command: %s\n" % kPluginCtxName)
		raise

# Uninitialize the script plug-in
def uninitializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject)
	try:
		mplugin.deregisterContextCommand(kPluginCtxName, kPluginCmdName)
	except:
		sys.stderr.write("Failed to deregister context command: %s\n" % kPluginCtxName)
		raise

