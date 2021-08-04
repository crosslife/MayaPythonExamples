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

#
# filmMoveManip.py
#	Scripted plug-in that displays a manipulator that 
# 	modifies the film translate horizontal and vertical
#	values. 
#
# To use this plug-in:
# 1. execute the following Python:
# import maya
# maya.cmds.loadPlugin("filmMoveManip.py")
# maya.cmds.spFilmMoveManipCtxCmd( 'spFilmMoveManipContext1' )
# maya.cmds.setParent( 'Shelf1' )
# maya.cmds.toolButton( 'spFilmMoveManip1', cl='toolCluster', t='spFilmMoveManipContext1', i1="filmMoveManip.xpm" )
# 2. Open the outliner and select a camera shape such as perspShape
# 3. A manipulator with a horizontal and vertical axis will be displayed.
# 4. Move the axis to modify the film translate
#
# A keyframing example:
# This plug-in uses dependentPlugsReset() and addDependentPlugs() to
# make the U and V translate values keyable via the manipulator. If you
# comment out the calls and try to set a key (e.g. by pressing the "s"
# key) you will get an error that no keyable values are associated with
# the manipulator. To demonstrate keyframing try the following:
#
# 5. Follow steps 1-4 above
# 6. In the Outliner, select perspShape, topShape and frontShape
# 7. In the Channel Control panel, make "Film Translate H" keyable
# 8. Drag each of the three manips horizontally in the viewport
# 9. Press the "s" key to set a keyframe
# 10.Select the three cameraShapes individually. Each should have
#    its Film Translate H value keyed
#

import sys
import manipulatorMath
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaRender as OpenMayaRender

filmMoveManipId = OpenMaya.MTypeId(0x8104B)
contextCmdName = "spFilmMoveManipCtxCmd"
nodeName = "spFilmMoveManip"

# class that holds geometry points
class manipulatorGeometry:
	scale = 3
	def horizontalStart(self):
	        p = OpenMaya.MPoint(0,0,0) * self.scale
	        # print "hstart: %g %g %g" % (p.x,p.y,p.z)
	        return p
	def horizontalEnd(self):
	        p = OpenMaya.MPoint(1,0,0) * self.scale
	        # print "hend:%g %g %g" % (p.x,p.y,p.z)
	        return p
	def verticalStart(self):
	        p = OpenMaya.MPoint(0,0,0) * self.scale
	        # print "vstart:%g %g %g" % (p.x,p.y,p.z)
	        return p
	def verticalEnd(self):
	        p = OpenMaya.MPoint(0,1,0) * self.scale
	        # print "vend: %g %g %g" % (p.x,p.y,p.z)
	        return p

# manipulator class
class filmMoveManip(OpenMayaMPx.MPxManipulatorNode):

	# Value indices
	horizontalIndex = 0
	verticalIndex = 0

	# GL names
	glHorizontalName = 0
	glVerticalName = 0

	# Manipulator translation
	translation = OpenMaya.MPoint()

	# Find the GL function table for the
	# draw method
	glRenderer = OpenMayaRender.MHardwareRenderer.theRenderer()
	glFT = glRenderer.glFunctionTable()

	def __init__(self):
		OpenMayaMPx.MPxManipulatorNode.__init__(self)

	def postConstructor(self):
		try:
			su = OpenMaya.MScriptUtil(0)
			iptr = su.asIntPtr()
			self.addDoubleValue( "horizontalValue", 0, iptr )
			self.horizontalIndex = su.getInt(iptr)
		except:
			sys.stderr.write("Failed to add horizontal double value\n")
			raise
			
		try:
			su = OpenMaya.MScriptUtil(0)
			iptr = su.asIntPtr()
			self.addDoubleValue( "verticalValue", 0, iptr )
			self.verticalIndex = su.getInt(iptr)
		except:
			sys.stderr.write("Failed to add vertical double value\n")
			raise

	def draw(self,view,dagpath,displayStyle,displayStatus):

		# get the 4 points of the manipulator
		mo = manipulatorGeometry()
		vs = mo.verticalStart()
		ve = mo.verticalEnd()
		hs = mo.horizontalStart()
		he = mo.horizontalEnd()
		
		# pre
		view.beginGL()
		self.glFT.glPushMatrix()
		self.glFT.glTranslated(self.translation.x,self.translation.y,self.translation.z)

		# get the first handle
		su = OpenMaya.MScriptUtil(0)
		iptr = su.asUintPtr()
		self.glFirstHandle( iptr )
		startIndex = su.getUint(iptr)

		# draw the manip
		self.glHorizontalName = startIndex
		self.colorAndName( view, self.glHorizontalName, True, self.mainColor() )
		self.glFT.glBegin( OpenMayaRender.MGL_LINES )
		self.glFT.glVertex3d( hs.x, hs.y, hs.z )
		self.glFT.glVertex3d( he.x, he.y, he.z )
		self.glFT.glEnd()		

		self.glVerticalName = self.glHorizontalName + 1
		self.colorAndName( view, self.glVerticalName, True, self.mainColor() )
		self.glFT.glBegin( OpenMayaRender.MGL_LINES )
		self.glFT.glVertex3d( vs.x, vs.y, vs.z )
		self.glFT.glVertex3d( ve.x, ve.y, ve.z )
		self.glFT.glEnd()		

		# post
		self.glFT.glPopMatrix()
		view.endGL()

	def doPress(self,view):
		self.translation = OpenMaya.MPoint()
		self.updateDragInformation(view)

	def doDrag(self,view):
		self.updateDragInformation(view)

	def doRelease(self,view):
		# Only update the attribute on release
		self.updateDragInformation(view,True)

	def getPlaneForView(self,view):
		mo = manipulatorGeometry()
		vs = mo.verticalStart()
		ve = mo.verticalEnd()
		hs = mo.horizontalStart()
		he = mo.horizontalEnd()
		v1 = he - hs
		v2 = vs - ve
		normal = v1 ^ v2
		normal.normalize()

		plane = manipulatorMath.planeMath()
		plane.setPlane( vs, normal )

		return plane

	def updateDragInformation(self,view,updateAttribute = False):
		# mouse point and direction
		localMousePoint = OpenMaya.MPoint()
		localMouseDirection = OpenMaya.MVector()
		self.mouseRay( localMousePoint, localMouseDirection )

		# plane that mouse will move in
		plane = self.getPlaneForView( view )

		# intersect mouse into plane
		mouseIntersect = OpenMaya.MPoint()
		(worked,mouseIntersect) = plane.intersect( localMousePoint, localMouseDirection )
		if not worked:
			print "Failed to intersect plane"
			return

		# restrict the point movement
		su = OpenMaya.MScriptUtil(0)
		uintptr = su.asUintPtr()
		self.glActiveName( uintptr )
		active = su.getUint(uintptr)

		mo = manipulatorGeometry()

		start = None
		end = None
		if active == self.glHorizontalName:
			start = mo.horizontalStart()
			end = mo.horizontalEnd()			
		elif active == self.glVerticalName:
			start = mo.verticalStart()
			end = mo.verticalEnd()			
		else:
			raise "Unknown GL active component"

		vstart_end = start - end
		line = manipulatorMath.lineMath()
		line.setLine( start, vstart_end )
		
		closestPoint = OpenMaya.MPoint()
		(worked,closestPoint) = line.closestPoint( mouseIntersect )
		if not worked:
			print "Failed to find closest point to line"
			return

		self.translation = closestPoint
		# print "mi: %g %g %g" % (mouseIntersect.x,mouseIntersect.y,mouseIntersect.z)

		if updateAttribute:
			m = manipulatorMath.maxOfAbsThree(closestPoint.x,closestPoint.y,closestPoint.z)
			m = m / 10.0 # slow down operation
			if active == self.glHorizontalName:
				self.setDoubleValue(self.horizontalIndex,m)
			elif active == self.glVerticalName:
				self.setDoubleValue(self.verticalIndex,m)

	def connectToDependNode(self, node):
		nodeFn = OpenMaya.MFnDependencyNode(node)

		try:
			hPlug = nodeFn.findPlug("filmTranslateH")
			vPlug = nodeFn.findPlug("filmTranslateV")

			su = OpenMaya.MScriptUtil(0)
			iptr = su.asIntPtr()
			self.connectPlugToValue( hPlug, self.horizontalIndex, iptr )
			self.connectPlugToValue( vPlug, self.verticalIndex, iptr )			

			# Mark the plugs keyable.
			self.addDependentPlug(hPlug)
			self.addDependentPlug(vPlug)
		except:
			sys.stderr.write( "Error finding and connecting plugs\n" )
			raise

		try:
			OpenMayaMPx.MPxManipulatorNode.finishAddingManips(self)
			OpenMayaMPx.MPxManipulatorNode.connectToDependNode(self,node)
		except:
			sys.stderr.write( "Error when finishing node connection\n" )
			raise


def filmMoveManipCreator():
	return OpenMayaMPx.asMPxPtr( filmMoveManip() )

def filmMoveManipInitialize():
	print "Initializing film move manipulator"

class filmMoveManipContext(OpenMayaMPx.MPxSelectionContext):
	def __init__(self):
		OpenMayaMPx.MPxSelectionContext.__init__(self)

	def toolOnSetup(self,event):
		updateManipulators(self)
		OpenMaya.MModelMessage.addCallback(OpenMaya.MModelMessage.kActiveListModified, updateManipulators, self)

def updateManipulators(clientData):
	clientData.deleteManipulators()
	selectionList = OpenMaya.MSelectionList()

	# Loop through the selection list, linking the film translate
	# plugs on each selected camera to the manipulator.
	OpenMaya.MGlobal.getActiveSelectionList(selectionList)
	selectionIter = OpenMaya.MItSelectionList(selectionList, OpenMaya.MFn.kInvalid)
	while not selectionIter.isDone():
		dependNode = OpenMaya.MObject()
		selectionIter.getDependNode(dependNode)
		if dependNode.isNull() or not dependNode.hasFn(OpenMaya.MFn.kCamera):
			print "depend node is null or not a camera"
			selectionIter.next()
			continue
			
		dependNodeFn = OpenMaya.MFnDependencyNode(dependNode)
		hPlug = dependNodeFn.findPlug("filmTranslateH", False)
		vPlug = dependNodeFn.findPlug("filmTranslateV", False)
		if hPlug.isNull() or vPlug.isNull():
			print "One of filmTranslate H,V plugs are null"
			selectionIter.next()
			continue

		manipObject = OpenMaya.MObject()
		manipulator = OpenMayaMPx.MPxManipulatorNode.newManipulator(nodeName, manipObject)
		if manipulator is not None:
			# Clear the list of keyable plugs.
			manipulator.dependentPlugsReset()

			clientData.addManipulator(manipObject)
			manipulator.connectToDependNode(dependNode)
		selectionIter.next()


class filmMoveManipCtxCmd(OpenMayaMPx.MPxContextCommand):
	def __init__(self):
		OpenMayaMPx.MPxContextCommand.__init__(self)

	def makeObj(self):
		return OpenMayaMPx.asMPxPtr( filmMoveManipContext() )


def contextCmdCreator():
	return OpenMayaMPx.asMPxPtr( filmMoveManipCtxCmd() )


# initialize the script plug-in
def initializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject)

	try:
		mplugin.registerContextCommand( contextCmdName, contextCmdCreator )
	except:
		print "Failed to register context command: %s" % contextCmdName
		raise
	
	try:
		mplugin.registerNode(nodeName, filmMoveManipId, filmMoveManipCreator, filmMoveManipInitialize, OpenMayaMPx.MPxNode.kManipulatorNode)
	except:
		print "Failed to register node: %s" % nodeName
		raise

# uninitialize the script plug-in
def uninitializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject)
	try:
		mplugin.deregisterContextCommand(contextCmdName)
	except:
		print "Failed to deregister context command: %s" % contextCmdName
		raise
		
	try:
		mplugin.deregisterNode(filmMoveManipId)
	except:
		print "Failed to deregister node: %s" % nodeName
		raise
