import type { ComponentType, SVGProps } from 'react';
import {
  BarChartIcon,
  CloudIcon,
  DocumentIcon,
  LadybugIcon,
  LeafIcon,
  OpenBookIcon,
  SunCloudIcon,
} from '@/components/Icons/FarmIcons';

type IconComponent = ComponentType<SVGProps<SVGSVGElement>>;

export interface QuickAction {
  id: string;
  title: string;
  description: string;
  href: string;
  tint: 'green' | 'blue' | 'orange' | 'purple';
  icon: IconComponent;
}

export const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'crop-advice',
    title: 'Crop Advice',
    description: 'Get AI recommendations',
    href: '/assistant',
    tint: 'green',
    icon: LeafIcon,
  },
  {
    id: 'weather-insights',
    title: 'Weather Insights',
    description: 'View detailed forecast',
    href: '/weather',
    tint: 'blue',
    icon: SunCloudIcon,
  },
  {
    id: 'pest-diagnosis',
    title: 'Pest Diagnosis',
    description: 'Identify plant issues',
    href: '/pest-disease',
    tint: 'orange',
    icon: LadybugIcon,
  },
  {
    id: 'farming-knowledge',
    title: 'Farming Knowledge',
    description: 'Learn best practices',
    href: '/knowledge',
    tint: 'purple',
    icon: OpenBookIcon,
  },
];

export interface ExampleQuestion {
  id: string;
  question: string;
  theme: 'crop' | 'pest' | 'weather';
}

export const EXAMPLE_QUESTIONS: ExampleQuestion[] = [
  { id: 'example-wheat', question: 'How to improve wheat yield?', theme: 'crop' },
  { id: 'example-leaf-spot', question: 'How to identify leaf spot in tomato?', theme: 'pest' },
  { id: 'example-rain', question: 'Will it rain this week in my area?', theme: 'weather' },
];

export const SAMPLE_TIP = {
  label: 'Sample tip',
  text: 'Good time for irrigation in the evening.',
};

export interface QuickTool {
  id: string;
  label: string;
  href: string;
  tint: 'red' | 'green' | 'orange' | 'purple';
  icon: IconComponent;
}

export const QUICK_TOOLS: QuickTool[] = [
  {
    id: 'disease-checker',
    label: 'Disease Checker',
    href: '/pest-disease',
    tint: 'red',
    icon: LadybugIcon,
  },
  {
    id: 'fertilizer-guide',
    label: 'Fertilizer Guide',
    href: '/knowledge?category=advisory',
    tint: 'green',
    icon: LeafIcon,
  },
  {
    id: 'market-prices',
    label: 'Market Prices',
    href: '/knowledge?category=market',
    tint: 'orange',
    icon: BarChartIcon,
  },
  {
    id: 'government-schemes',
    label: 'Government Schemes',
    href: '/knowledge?category=schemes',
    tint: 'purple',
    icon: DocumentIcon,
  },
];

export const QUESTION_THEME_ICONS: Record<ExampleQuestion['theme'], IconComponent> = {
  crop: LeafIcon,
  pest: LadybugIcon,
  weather: CloudIcon,
};

export function getQuestionTheme(question: string): ExampleQuestion['theme'] {
  const text = question.toLowerCase();
  if (/(pest|disease|leaf spot|aphid|fungus|insect|bug)/.test(text)) return 'pest';
  if (/(rain|weather|forecast|temperature|monsoon|humidity)/.test(text)) return 'weather';
  return 'crop';
}
