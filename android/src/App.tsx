import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { View, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { Provider as PaperProvider } from 'react-native-paper';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { ThemeProvider } from './theme';
import ChatInterface from './components/ChatInterface';
import WeatherCard from './components/WeatherCard';
import ResourcesList from './components/ResourcesList';

const Stack = createStackNavigator();

const App = () => {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PaperProvider>
        <ThemeProvider>
          <NavigationContainer>
            <StatusBar style="light" backgroundColor="#14532D" />
            <Stack.Navigator
              screenOptions={{
                headerStyle: { backgroundColor: '#14532D' },
                headerTintColor: '#FFFFFF',
                headerTitleStyle: { fontWeight: '600' },
              }}
            >
              <Stack.Screen
                name="Chat"
                component={ChatScreen}
                options={{ title: 'MyFarm AI' }}
              />
              <Stack.Screen
                name="Weather"
                component={WeatherScreen}
                options={{ title: 'Weather' }}
              />
              <Stack.Screen
                name="Resources"
                component={ResourcesScreen}
                options={{ title: 'Resources' }}
              />
            </Stack.Navigator>
          </NavigationContainer>
        </ThemeProvider>
      </PaperProvider>
    </GestureHandlerRootView>
  );
};

const ChatScreen = () => (
  <ChatInterface weatherContext={null} />
);

const WeatherScreen = () => {
  return (
    <View style={styles.weatherScreen}>
      <WeatherCard latitude={28.6139} longitude={77.2090} />
    </View>
  );
};

const ResourcesScreen = () => (
  <View style={styles.resourcesScreen}>
    <ResourcesList />
  </View>
);

const styles = StyleSheet.create({
  weatherScreen: {
    flex: 1,
    padding: 16,
  },
  resourcesScreen: {
    flex: 1,
  },
});

export default App;