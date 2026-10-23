'use client';

import { useWeather } from '@/hooks/useWeather';
import { getWeatherDescription } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui';
import { Badge } from '@/components/ui';
import { Skeleton } from '@/components/ui';
import {
  Sun,
  Cloud,
  CloudRain,
  CloudSnow,
  CloudLightning,
  CloudDrizzle,
  CloudFog,
  Wind,
} from 'lucide-react';

interface ForecastDay {
  date: string;
  weathercode: number;
  temperature_2m_max: number;
  temperature_2m_min: number;
  precipitation_probability_max: number;
}

interface WeatherCardProps {
  latitude: number;
  longitude: number;
}

function getWeatherIcon(code: number) {
  switch (true) {
    case code === 0:
      return Sun;
    case code === 1:
      return Sun;
    case code === 2:
    case code === 3:
      return Cloud;
    case code === 45:
    case code === 48:
      return CloudFog;
    case code === 51:
    case code === 53:
    case code === 55:
      return CloudDrizzle;
    case code === 56:
    case code === 57:
      return CloudRain;
    case code === 61:
    case code === 63:
    case code === 65:
      return CloudRain;
    case code === 66:
    case code === 67:
      return CloudRain;
    case code === 71:
    case code === 73:
    case code === 75:
      return CloudSnow;
    case code === 77:
      return CloudSnow;
    case code === 80:
    case code === 81:
    case code === 82:
      return CloudRain;
    case code === 85:
    case code === 86:
      return CloudSnow;
    case code === 95:
      return CloudLightning;
    case code === 96:
    case code === 99:
      return CloudLightning;
    default:
      return Cloud;
  }
}

export function WeatherCard({ latitude, longitude }: WeatherCardProps) {
  const { currentWeather, forecast, isLoading, error } = useWeather(latitude, longitude);

  if (isLoading) {
    return (
      <Card variant="default">
        <CardContent className="space-y-4 p-4">
          <Skeleton variant="rectangular" className="h-6 w-1/4" />
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} variant="rectangular" className="h-20 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card variant="outlined">
        <CardContent className="p-4 text-center">
          <p className="text-body-medium text-error">Failed to load weather</p>
        </CardContent>
      </Card>
    );
  }

  if (!currentWeather) return null;

  const WeatherIcon = getWeatherIcon(currentWeather.weathercode);
  const description = getWeatherDescription(currentWeather.weathercode);

  return (
    <Card variant="default">
      <CardContent className="space-y-4 p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-headline-small font-semibold text-on-surface">Current Weather</h3>
          <span className="text-body-small text-on-surface-variant">
            {new Date(currentWeather.time).toLocaleTimeString()}
          </span>
        </div>

        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-display-small font-bold text-on-surface">{currentWeather.temperature}°C</p>
            <p className="text-body-small text-on-surface-variant">Temperature</p>
          </div>
          <div>
            <p className="text-display-small font-bold text-on-surface">{currentWeather.windspeed} km/h</p>
            <p className="text-body-small text-on-surface-variant">Wind</p>
          </div>
          <div className="flex flex-col items-center justify-center gap-1">
            <WeatherIcon className="w-8 h-8 text-on-surface" aria-hidden="true" />
            <p className="text-body-small font-medium text-on-surface">{description}</p>
          </div>
          <div>
            <p className="text-display-small font-bold text-on-surface">{description}</p>
          </div>
        </div>

        {forecast && forecast.length > 0 && (
          <div>
            <h4 className="text-headline-small font-medium text-on-surface mb-2">7-Day Forecast</h4>
            <div className="grid grid-cols-7 gap-2 overflow-x-auto pb-2">
              {forecast.slice(0, 7).map((day: ForecastDay) => (
                <div
                  key={day.date}
                  className="min-w-[80px] rounded-lg border border-outline p-3 text-center bg-surface-container"
                >
                  <p className="text-label-medium font-medium text-on-surface">
                    {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                  </p>
                  <Badge variant="outline" className="mb-1 mx-auto max-w-full">
                    {getWeatherDescription(day.weathercode)}
                  </Badge>
                  <p className="text-body-small font-medium text-on-surface">
                    {day.temperature_2m_max}°/{day.temperature_2m_min}°
                  </p>
                  <p className="text-label-small text-on-surface-variant">
                    {day.precipitation_probability_max}% rain
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default WeatherCard;