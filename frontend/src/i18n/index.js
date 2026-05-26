import { createI18n } from 'vue-i18n';
import zhCN from '../locales/zh-CN';
import enUS from '../locales/en-US';

// 从localStorage获取保存的语言，默认中文
const getSavedLocale = () => {
  try {
    const savedAppearance = localStorage.getItem('appearance');
    if (savedAppearance) {
      const appearance = JSON.parse(savedAppearance);
      return appearance.language || 'zh-CN';
    }
  } catch (error) {
    console.error('读取语言设置失败:', error);
  }
  return 'zh-CN';
};

const i18n = createI18n({
  legacy: false, // 使用 Composition API 模式
  locale: getSavedLocale(),
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  }
});

export default i18n;

// 切换语言的辅助函数
export const setLocale = (locale) => {
  i18n.global.locale.value = locale;
  
  // 保存到localStorage
  try {
    const savedAppearance = localStorage.getItem('appearance');
    const appearance = savedAppearance ? JSON.parse(savedAppearance) : {};
    appearance.language = locale;
    localStorage.setItem('appearance', JSON.stringify(appearance));
  } catch (error) {
    console.error('保存语言设置失败:', error);
  }
};