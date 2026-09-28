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
  const [loading, setLoading] = useState(true);
  const [vpsData, setVpsData] = useState(null);
  const [heading, setHeading] = useState(0.0);
  const [error, setError] = useState(null);

  const lat = location?.latitude || 12.9716;
  const lon = location?.longitude || 77.5946;

  useEffect(() => {
    if (visible) {
      fetchMetadata(heading);
    }
  }, [visible, lat, lon]);

  const fetchMetadata = async (h = 0.0) => {
    setLoading(true);
    setError(null);
    try {
      const data = await ApiService.getVpsMetadata(lat, lon, h);
      setVpsData(data);
      if (!data.available) {
        setError(data.message || '360° visual coverage is unavailable at this location.');
      }
    } catch (e) {
      setError('360° visual coverage is unavailable at this location.');
    } finally {
      setLoading(false);
    }
  };

  const changeHeading = (newHeading) => {
    setHeading(newHeading);
    fetchMetadata(newHeading);
  };

  const embedUrl = vpsData?.embed_url || `https://maps.google.com/maps?q=&layer=c&cbll=${lat},${lon}&cbp=11,${heading},0,0,0&output=embed`;

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
              GPS: {lat.toFixed(5)}°, {lon.toFixed(5)}° • En route to {destinationName}
            </Text>
          </View>
          <TouchableOpacity style={styles.closeBtn} onPress={onClose} activeOpacity={0.8}>
            <Text style={styles.closeBtnText}>Return to Map 🗺️</Text>
          </TouchableOpacity>
        </View>

        {/* Orientation Controls */}
        <View style={styles.orientationBar}>
          <Text style={styles.orientationLabel}>CAMERA ANGLE:</Text>
          <TouchableOpacity
            style={[styles.angleBtn, heading === 0 && styles.angleBtnActive]}
            onPress={() => changeHeading(0)}
          >
            <Text style={[styles.angleText, heading === 0 && styles.angleTextActive]}>⬆️ North</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.angleBtn, heading === 90 && styles.angleBtnActive]}
            onPress={() => changeHeading(90)}
          >
            <Text style={[styles.angleText, heading === 90 && styles.angleTextActive]}>➡️ East</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.angleBtn, heading === 180 && styles.angleBtnActive]}
            onPress={() => changeHeading(180)}
          >
            <Text style={[styles.angleText, heading === 180 && styles.angleTextActive]}>⬇️ South</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.angleBtn, heading === 270 && styles.angleBtnActive]}
            onPress={() => changeHeading(270)}
          >
            <Text style={[styles.angleText, heading === 270 && styles.angleTextActive]}>⬅️ West</Text>
          </TouchableOpacity>
        </View>

        {/* Content Area */}
        <View style={styles.content}>
          {loading && (
            <View style={styles.centerContainer}>
              <ActivityIndicator size="large" color={COLORS.primaryLight} />
              <Text style={styles.loadingText}>Fetching 360° Visual Positioning imagery…</Text>
            </View>
          )}

          {!loading && error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorIcon}>📡</Text>
              <Text style={styles.errorTitle}>Visual Coverage Unavailable</Text>
              <Text style={styles.errorText}>{error}</Text>
              <TouchableOpacity style={styles.returnButton} onPress={onClose}>
                <Text style={styles.returnButtonText}>Return to Normal Map Navigation</Text>
              </TouchableOpacity>
            </View>
          )}

          {!loading && !error && (
            <WebView
              source={{ uri: embedUrl }}
              style={styles.webview}
              javaScriptEnabled={true}
              domStorageEnabled={true}
              startInLoadingState={true}
              renderLoading={() => (
                <View style={styles.centerContainer}>
                  <ActivityIndicator size="large" color={COLORS.primaryLight} />
                </View>
              )}
            />
          )}
        </View>

        {/* Bottom Safety Info Bar */}
        <View style={styles.bottomBar}>
          <Text style={styles.bottomText}>
            💡 Interactive 360° Google Visual View • Drag to inspect surroundings & safety lighting.
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
