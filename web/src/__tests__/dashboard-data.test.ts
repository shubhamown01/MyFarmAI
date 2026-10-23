import {
  EXAMPLE_QUESTIONS,
  getQuestionTheme,
  QUICK_ACTIONS,
  QUICK_TOOLS,
} from '@/lib/dashboard-data';

describe('dashboard data', () => {
  it('labels the required example questions', () => {
    expect(EXAMPLE_QUESTIONS.map((item) => item.question)).toEqual([
      'How to improve wheat yield?',
      'How to identify leaf spot in tomato?',
      'Will it rain this week in my area?',
    ]);
  });

  it('routes every quick action and tool to a real in-app page', () => {
    const hrefs = [
      ...QUICK_ACTIONS.map((item) => item.href),
      ...QUICK_TOOLS.map((item) => item.href),
    ];
    const allowedRoots = [
      '/assistant',
      '/weather',
      '/pest-disease',
      '/knowledge',
    ];

    hrefs.forEach((href) => {
      expect(allowedRoots.some((root) => href === root || href.startsWith(`${root}?`))).toBe(true);
    });
  });

  it('classifies questions for the right icon', () => {
    expect(getQuestionTheme('How to identify leaf spot in tomato?')).toBe('pest');
    expect(getQuestionTheme('Will it rain this week?')).toBe('weather');
    expect(getQuestionTheme('How to improve wheat yield?')).toBe('crop');
  });
});
