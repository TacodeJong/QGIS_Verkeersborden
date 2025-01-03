# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VerkeersbordenDialog
                                 A QGIS plugin
 Verkeersborden importeren
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-02-15
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Taco de Jong
        email                : taco@tictaco.nl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import csv
import requests
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QLineEdit, QCompleter
from PyQt5.QtCore import QStringListModel, Qt

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Verkeersborden_dialog_base.ui'))


class VerkeersbordenDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(VerkeersbordenDialog, self).__init__(parent)
        self.setupUi(self)  # Set up the user interface from Designer.
        self.fetchDataButton.clicked.connect(self.loadData)
        # Load and store municipalities data
        self.municipalities = self.loadMunicipalities()
        # Setup autocomplete
        self.setupAutocomplete()  # Ensure this is called after setupUi

    # def loadMunicipalities(self):
    #     municipalities = {}
    #     csv_path = os.path.join(os.path.dirname(__file__), 'data', 'gemeenten.csv')  # Adjust path as necessary
        
    #     with open(csv_path, mode='r', encoding='utf-8') as csvfile:
    #         reader = csv.DictReader(csvfile)
    #         for row in reader:
    #             municipalities[row['gemeentenaam']] = row['town-code']
        
    def loadMunicipalities(self):
        import datetime
        import requests

        municipalities = {}
        current_year = datetime.datetime.now().year
        
        for year in range(current_year, current_year - 2, -1):
            url = f"https://service.pdok.nl/cbs/gebiedsindelingen/{year}/wfs/v1_0?request=GetFeature&service=WFS&version=1.1.0&outputFormat=application%2Fjson&typeName=gebiedsindelingen%3Agemeente_gegeneraliseerd"

            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data['features']:
                    for feature in data['features']:
                        statnaam = feature['properties']['statnaam']
                        statcode = feature['properties']['statcode']
                        municipalities[statnaam] = statcode
                    print(f"Successfully fetched municipalities data for year {year}")
                    return municipalities
            
            print(f"No data available for year {year}, trying previous year")
        
        print("Failed to fetch municipalities data for current and previous year")
        return municipalities


    def setupAutocomplete(self):
        # Assuming self.municipalities is already populated
        completer = QCompleter(list(self.municipalities.keys()))
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setCompletionMode(QCompleter.PopupCompletion)

        # Assuming 'lineEditMunicipality' is your QLineEdit for the municipality input in your UI
        self.townCodeLineEdit.setCompleter(completer)

    def loadData(self):
        from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsProject, QgsField, QgsPointXY
        from PyQt5.QtCore import QVariant

        # Use user inputs for these variables

        # Construct the path to the embedded QML file
        current_dir = os.path.dirname(__file__)  # Get the directory of the current file
        qml_path = os.path.join(current_dir, "styles", "style.qml")  # Adjust the path to your QML file

        # QMessageBox.warning(None, "Stijl", f"Stijl van bestand: {qml_path}")
        selected_municipality_name = self.townCodeLineEdit.text()  # Assuming you have a QLineEdit for town code
        # Retrieve the corresponding town-code using the selected name
        town_code = self.municipalities.get(selected_municipality_name, None)

        style_path = qml_path
        layer_name = self.layerNameLineEdit.text()  # Assuming you have a QLineEdit for layer name
        
        # Adjust the URL to use the town_code variable
        url = f'https://data.ndw.nu/api/rest/static-road-data/traffic-signs/v3/current-state?town-code={town_code}&content-type=geo%2Bjson'

        response = requests.get(url)
        if response.status_code == 200:
            geojson_dict = response.json()
            vl = QgsVectorLayer("Point?crs=epsg:4326", layer_name, "memory")
            # The rest of your logic goes here...

            pr = vl.dataProvider()

            # Add fields to your layer based on the GeoJSON structure
            pr.addAttributes([
                QgsField("supplierId", QVariant.Int),
                QgsField("type", QVariant.String),
                QgsField("schemaVersion", QVariant.String),
                QgsField("validated", QVariant.String),
                QgsField("rvvCode", QVariant.String),
                QgsField("placement", QVariant.String),
                QgsField("side", QVariant.String),
                QgsField("bearing", QVariant.Double),
                QgsField("roadName", QVariant.String),
                QgsField("wvkId", QVariant.String),
                QgsField("countyName", QVariant.String),
                QgsField("countyCode", QVariant.String),
                QgsField("townName", QVariant.String),
                QgsField("image", QVariant.String),
                QgsField("firstSeen", QVariant.String),
                QgsField("lastSeen", QVariant.String),
                QgsField("publicationTimestamp", QVariant.String),
                # Add more fields as needed
            ])
            vl.updateFields()

            # Iterate through the features in the GeoJSON and add them to the layer
            for feature in geojson_dict['features']:
                # Create a new feature for the layer
                fet = QgsFeature()
                # Set the geometry for the feature using the coordinates from the GeoJSON
                fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(feature['geometry']['coordinates'][0], feature['geometry']['coordinates'][1])))
                # Set the attributes for the feature based on the GeoJSON properties
                fet.setAttributes([
                    feature['properties'].get('supplierId', 0),
                    feature['properties'].get('type', ''),
                    feature['properties'].get('schemaVersion', ''),
                    feature['properties'].get('validated', ''),
                    feature['properties'].get('rvvCode', ''),
                    feature['properties'].get('placement', ''),
                    feature['properties'].get('side', ''),
                    feature['properties'].get('bearing', 0.0),
                    feature['properties'].get('roadName', ''),
                    feature['properties'].get('wvkId', ''),
                    feature['properties'].get('countyName', ''),
                    feature['properties'].get('countyCode', ''),
                    feature['properties'].get('townName', ''),
                    feature['properties'].get('image', ''),
                    feature['properties'].get('firstSeen', ''),
                    feature['properties'].get('lastSeen', ''),
                    feature['properties'].get('publicationTimestamp', ''),
                ])
                # Add the feature to the provider
                pr.addFeature(fet)
            # Add the layer to the QGIS interface
            QgsProject.instance().addMapLayer(vl)

            # Load style from the specified QML file
            result, error = vl.loadNamedStyle(style_path)
            if not result:
                print("Error loading style:", error)
            else:
                vl.triggerRepaint()
        else:
            print("Failed to fetch the GeoJSON data.")
