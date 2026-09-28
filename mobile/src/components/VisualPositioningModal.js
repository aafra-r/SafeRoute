import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  SafeAreaView
} from 'react-native';
import { WebView } from 'react-native-webview';
import { COLORS } from '../theme/colors';
import { ApiService } from '../services/api';

export const VisualPositioningModal = ({
  visible = false,
  onClose,
  location = null,
  destinationName = 'Destination'
}) => {
  const [heading, setHeading] = useState(0.0);
  const [steppedMeters, setSteppedMeters] = useState(0);
  
  const baseLat = location?.latitude || 10.7905;
  const baseLon = location?.longitude || 78.7047;

  const [currentLat, setCurrentLat] = useState(baseLat);
  const [currentLon, setCurrentLon] = useState(baseLon);

  useEffect(() => {
    if (visible) {
      setCurrentLat(baseLat);
      setCurrentLon(baseLon);
      setSteppedMeters(0);
      setHeading(0.0);
    }
  }, [visible, baseLat, baseLon]);

  const stepPosition = (distanceMeters) => {
    setSteppedMeters(prev => prev + distanceMeters);
    const rad = heading * (Math.PI / 180);
    const deltaLat = (distanceMeters * Math.cos(rad)) / 111000;
    const deltaLon = (distanceMeters * Math.sin(rad)) / (111000 * Math.cos(currentLat * (Math.PI / 180)));
    setCurrentLat(prev => prev + deltaLat);
    setCurrentLon(prev => prev + deltaLon);
  };

  const rotateHeading = (deltaDegrees) => {
    setHeading(prev => (prev + deltaDegrees + 360) % 360);
  };

  const resetPosition = () => {
    setCurrentLat(baseLat);
    setCurrentLon(baseLon);
    setHeading(0.0);
    setSteppedMeters(0);
  };

  const embedUrl = `https://maps.google.com/maps?q=${currentLat},${currentLon}&layer=c&cbll=${currentLat},${currentLon}&cbp=12,${heading},0,0,0&output=embed`;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={false}
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.container}>
        {/* Header Bar */}
        <View style={styles.header}>
          <View style={styles.headerTitleCol}>
            <View style={styles.badgeRow}>
              <Text style={styles.vpsBadge}>👁️ 360° VISUAL POSITIONING</Text>
              <Text style={styles.activeDot}>● LIVE</Text>
            </View>
            <Text style={styles.headerTitle}>Street-Level Surroundings</Text>
            <Text style={styles.headerCoords}>
              GPS: {currentLat.toFixed(5)}°, {currentLon.toFixed(5)}° • En route to {destinationName}
            </Text>
          </View>
          <TouchableOpacity style={styles.closeBtn} onPress={onClose} activeOpacity={0.8}>
            <Text style={styles.closeBtnText}>Return to Map 🗺️</Text>
          </TouchableOpacity>
        </View>

        {/* Directional Stepping Bar */}
        <View style={styles.orientationBar}>
          <TouchableOpacity style={[styles.angleBtn, { backgroundColor: COLORS.safeGreen }]} onPress={() => stepPosition(15)}>
            <Text style={[styles.angleText, { color: '#FFF' }]}>⬆️ +15m</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.angleBtn, { backgroundColor: COLORS.warningYellow }]} onPress={() => stepPosition(-15)}>
            <Text style={[styles.angleText, { color: '#FFF' }]}>⬇️ -15m</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.angleBtn} onPress={() => rotateHeading(-45)}>
            <Text style={styles.angleText}>↺ Left</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.angleBtn} onPress={() => rotateHeading(45)}>
            <Text style={styles.angleText}>↻ Right</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.angleBtn, { backgroundColor: 'transparent', borderWidth: 1, borderColor: '#334155' }]} onPress={resetPosition}>
            <Text style={styles.angleText}>🧭 Reset</Text>
          </TouchableOpacity>
        </View>

        {/* Content Area */}
        <View style={styles.content}>
          <WebView
            source={{ uri: embedUrl }}
            style={styles.webview}
            javaScriptEnabled={true}
            domStorageEnabled={true}
            startInLoadingState={true}
            renderLoading={() => (
              <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color={COLORS.primaryLight} />
                <Text style={styles.loadingText}>Fetching 360° Visual Positioning imagery…</Text>
              </View>
            )}
          />
        </View>

        {/* Bottom Safety Info Bar */}
        <View style={styles.bottomBar}>
          <Text style={styles.bottomText}>
            💡 Interactive 360° Google Visual View • Drag to inspect surroundings & tap +15m / Turn to move on road ({steppedMeters >= 0 ? '+' : ''}{steppedMeters}m).
          </Text>
        </View>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#070A12'
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#0F172A',
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B'
  },
  headerTitleCol: {
    flex: 1
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6
  },
  vpsBadge: {
    color: COLORS.primaryLight,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5
  },
  activeDot: {
    color: COLORS.safeGreen,
    fontSize: 9,
    fontWeight: '800'
  },
  headerTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
    marginTop: 2
  },
  headerCoords: {
    color: COLORS.textMuted,
    fontSize: 11,
    marginTop: 1
  },
  closeBtn: {
    backgroundColor: 'rgba(59, 130, 246, 0.18)',
    borderColor: COLORS.primaryLight,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10
  },
  closeBtnText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700'
  },
  orientationBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#0B1120',
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
    gap: 6
  },
  orientationLabel: {
    color: COLORS.textMuted,
    fontSize: 9,
    fontWeight: '800',
    marginRight: 2
  },
  angleBtn: {
    flex: 1,
    backgroundColor: '#1E293B',
    paddingVertical: 6,
    borderRadius: 8,
    alignItems: 'center'
  },
  angleBtnActive: {
    backgroundColor: COLORS.primary
  },
  angleText: {
    color: COLORS.textMuted,
    fontSize: 10,
    fontWeight: '700'
  },
  angleTextActive: {
    color: '#FFFFFF'
  },
  content: {
    flex: 1,
    backgroundColor: '#000000'
  },
  webview: {
    flex: 1,
    backgroundColor: '#000000'
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#070A12'
  },
  loadingText: {
    color: COLORS.textSecondary,
    fontSize: 13,
    marginTop: 12,
    textAlign: 'center'
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#070A12'
  },
  errorIcon: {
    fontSize: 44,
    marginBottom: 12
  },
  errorTitle: {
    color: COLORS.warningYellow,
    fontSize: 17,
    fontWeight: '800',
    marginBottom: 6
  },
  errorText: {
    color: COLORS.textMuted,
    fontSize: 13,
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 18
  },
  returnButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 12
  },
  returnButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '800'
  },
  bottomBar: {
    backgroundColor: '#0F172A',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#1E293B'
  },
  bottomText: {
    color: COLORS.textMuted,
    fontSize: 11,
    textAlign: 'center'
  }
});
