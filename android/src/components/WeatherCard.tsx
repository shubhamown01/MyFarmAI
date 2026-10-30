import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useWeather } from '../hooks/useWeather';
import { WEATHER_CODES } from '../utils/weatherCodes';
import { useTheme } from '../theme';

interface WeatherCardProps {
  latitude: number;
  longitude: number;
}

export const WeatherCard: React.FC<WeatherCardProps> = ({
  latitude,
  longitude,
}) => {
  const { weather, isLoading, error, fetchWeather } = useWeather();
  React.useEffect(() => {
    fetchWeather(latitude, longitude);
  }, [fetchWeather, latitude, longitude]);

  const currentWeather = weather?.current_weather;
  const forecast = weather?.daily;
  const { colors } = useTheme();

  if (isLoading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: colors.surfaceContainer }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.errorContainer, { backgroundColor: colors.errorContainer }]}>
        <Text style={[styles.errorText, { color: colors.onErrorContainer }]}>Failed to load weather</Text>
      </View>
    );
  }

  if (!currentWeather) return null;

  return (
    <View style={[styles.card, { backgroundColor: colors.surfaceContainer, shadowColor: colors.shadow }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.primary }]}>Current Weather</Text>
        <Text style={[styles.time, { color: colors.onSurfaceVariant }]}>
          {new Date(currentWeather.time).toLocaleTimeString()}
        </Text>
      </View>

      <View style={styles.currentWeather}>
        <View style={[styles.weatherItem, { backgroundColor: colors.surfaceContainerLow }]}>
          <Text style={[styles.value, { color: colors.primary }]}>{currentWeather.temperature}°C</Text>
          <Text style={[styles.label, { color: colors.onSurfaceVariant }]}>Temperature</Text>
        </View>
        <View style={[styles.weatherItem, { backgroundColor: colors.surfaceContainerLow }]}>
          <Text style={[styles.value, { color: colors.primary }]}>{currentWeather.windspeed} km/h</Text>
          <Text style={[styles.label, { color: colors.onSurfaceVariant }]}>Wind</Text>
        </View>
        <View style={[styles.weatherItem, { backgroundColor: colors.surfaceContainerLow }]}>
          <Text style={[styles.value, { color: colors.primary }]}>{currentWeather.weathercode}</Text>
          <Text style={[styles.label, { color: colors.onSurfaceVariant }]}>Code</Text>
        </View>
        <View style={[styles.weatherItem, { backgroundColor: colors.surfaceContainerLow }]}>
          <Text style={[styles.value, { color: colors.primary }]}>
            {WEATHER_CODES[currentWeather.weathercode] || 'Unknown'}
          </Text>
        </View>
      </View>

      {forecast && forecast.length > 0 && (
        <View>
          <Text style={[styles.sectionTitle, { color: colors.onSurface }]}>7-Day Forecast</Text>
          <View style={styles.forecastContainer}>
            {forecast.slice(0, 7).map((day) => (
              <View key={day.date} style={[styles.forecastItem, { backgroundColor: colors.surfaceContainerLow }]}>
                <Text style={[styles.forecastDay, { color: colors.onSurface }]}>
                  {new Date(day.date).toLocaleDateString('en-US', {
                    weekday: 'short',
                  })}
                </Text>
                <Text style={[styles.forecastDesc, { color: colors.onSurfaceVariant }]}>
                  {WEATHER_CODES[day.weathercode] || 'Unknown'}
                </Text>
                <Text style={[styles.forecastTemp, { color: colors.primary }]}>
                  {day.temperature_2m_max}°/{day.temperature_2m_min}°
                </Text>
                <Text style={[styles.forecastRain, { color: colors.onSurfaceVariant }]}>
                  {day.precipitation_probability_max}% rain
                </Text>
              </View>
            ))}
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
  },
  time: {
    fontSize: 12,
  },
  currentWeather: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  weatherItem: {
    flex: 1,
    minWidth: '45%',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  value: {
    fontSize: 20,
    fontWeight: '600',
  },
  label: {
    fontSize: 12,
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  forecastContainer: {
    gap: 8,
  },
  forecastItem: {
    minWidth: 80,
    padding: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  forecastDay: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
  },
  forecastDesc: {
    fontSize: 11,
    marginBottom: 4,
  },
  forecastTemp: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 4,
  },
  forecastRain: {
    fontSize: 11,
  },
  loadingContainer: {
    padding: 32,
    alignItems: 'center',
  },
  errorContainer: {
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  errorText: {
    fontSize: 14,
  },
});

export default WeatherCard;