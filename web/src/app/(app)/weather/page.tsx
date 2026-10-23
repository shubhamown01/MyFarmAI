import type { Metadata } from 'next';
import { WeatherView } from './WeatherView';

export const metadata: Metadata = {
  title: 'Weather',
};

export default function WeatherPage() {
  return <WeatherView />;
}
