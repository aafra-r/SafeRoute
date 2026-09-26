import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { COLORS } from '../theme/colors';
import { Header } from '../components/Header';
import { Button } from '../components/Button';
import { useAuth } from '../context/AuthContext';

export const LoginScreen = ({ navigation }) => {
  const { login, loading } = useAuth();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async () => {
    if (!identifier.trim() || !password) {
      setError('Please enter both your email/mobile and password.');
      return;
    }
    setError('');
    const res = await login(identifier.trim(), password);
    if (res.success) {
      // AuthContext updates isAuthenticated, triggering navigator redirect
    } else {
      if (res.error && res.error.includes('unverified')) {
        navigation.navigate('VerifyOtp');
      } else {
        setError(res.error || 'Login failed. Please check your credentials.');
      }
    }
  };

  const handleGuestAccess = async () => {
    setIdentifier('demo@saferoute.app');
    setPassword('demo1234');
    setError('');
    const res = await login('demo@saferoute.app', 'demo1234');
    if (!res.success) {
      setError(res.error || 'Guest login failed');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      <Header title="Welcome Back" subtitle="Log in to access your trusted safety features" />

      <View style={styles.formCard}>
        <Text style={styles.formTitle}>SafeRoute Account</Text>
        <Text style={styles.formSubtitle}>Sign in with your email or mobile number</Text>

        {error ? (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        ) : null}

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Email or Mobile Number</Text>
          <TextInput
            style={styles.input}
            value={identifier}
            onChangeText={setIdentifier}
            placeholder="e.g. name@example.com or +919876543210"
            placeholderTextColor={COLORS.textMuted}
            keyboardType="email-address"
            autoCapitalize="none"
          />
        </View>

        <View style={styles.inputGroup}>
          <View style={styles.labelRow}>
            <Text style={styles.label}>Password</Text>
            <TouchableOpacity onPress={() => navigation.navigate('ForgotPassword')}>
              <Text style={styles.forgotLink}>Forgot Password?</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.passwordWrapper}>
            <TextInput
              style={[styles.input, { flex: 1 }]}
              value={password}
              onChangeText={setPassword}
              placeholder="••••••••"
              placeholderTextColor={COLORS.textMuted}
              secureTextEntry={!showPassword}
            />
            <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={styles.eyeBtn}>
              <Text style={styles.eyeIcon}>{showPassword ? '🙈' : '👁️'}</Text>
            </TouchableOpacity>
          </View>
        </View>

        <Button
          title="Log In ›"
          onPress={handleLogin}
          loading={loading}
          disabled={loading}
          style={{ marginTop: 10 }}
        />

        <Button
          title="⚡ 1-Click Guest Access"
          onPress={handleGuestAccess}
          variant="warning"
          disabled={loading}
          style={{ marginTop: 10 }}
        />

        <TouchableOpacity onPress={() => navigation.navigate('Register')} style={styles.linkRow}>
          <Text style={styles.linkText}>Don't have an account? <Text style={styles.linkHighlight}>Create Account</Text></Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background
  },
  scrollContent: {
    padding: 16
  },
  formCard: {
    backgroundColor: COLORS.surfaceCard,
    borderRadius: 16,
    padding: 20,
    marginTop: 16,
    borderWidth: 1,
    borderColor: COLORS.border
  },
  formTitle: {
    color: COLORS.textPrimary,
    fontSize: 18,
    fontWeight: '700'
  },
  formSubtitle: {
    color: COLORS.textSecondary,
    fontSize: 12,
    marginTop: 4,
    marginBottom: 16
  },
  errorBox: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    borderColor: COLORS.dangerRed,
    borderWidth: 1,
    borderRadius: 10,
    padding: 10,
    marginBottom: 14
  },
  errorText: {
    color: '#FCA5A5',
    fontSize: 12,
    fontWeight: '600'
  },
  inputGroup: {
    marginBottom: 14
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6
  },
  label: {
    color: COLORS.textSecondary,
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5
  },
  forgotLink: {
    color: COLORS.primaryLight,
    fontSize: 11,
    fontWeight: '700'
  },
  input: {
    backgroundColor: '#090E1A',
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 10,
    color: '#ffffff',
    padding: 12,
    fontSize: 14
  },
  passwordWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    position: 'relative'
  },
  eyeBtn: {
    position: 'absolute',
    right: 12,
    padding: 4
  },
  eyeIcon: {
    fontSize: 16
  },
  linkRow: {
    marginTop: 20,
    alignItems: 'center'
  },
  linkText: {
    color: COLORS.textSecondary,
    fontSize: 13
  },
  linkHighlight: {
    color: COLORS.primaryLight,
    fontWeight: '700'
  }
});
