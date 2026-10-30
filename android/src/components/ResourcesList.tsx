import React, { useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  TextInput,
} from 'react-native';
import { useResources } from '../hooks/useResources';
import { useTheme } from '../theme';
import { Linking } from 'react-native';

export const ResourcesList: React.FC = () => {
  const {
    resources,
    categories,
    selectedCategory: category,
    setCategory,
    isLoading,
    error,
    fetchResources,
    fetchCategories,
  } = useResources();
  const [searchQuery, setSearchQuery] = useState('');
  const { colors } = useTheme();

  React.useEffect(() => {
    fetchResources();
    fetchCategories();
  }, [fetchResources, fetchCategories]);

  const filteredResources = resources.filter((resource) => {
    const matchesCategory = !category || resource.category === category;
    const matchesSearch = resource.title
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

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
        <Text style={[styles.errorText, { color: colors.onErrorContainer }]}>Failed to load resources</Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.surface }]}>
      <View style={[styles.header, { backgroundColor: colors.surfaceContainer, borderBottomColor: colors.outline }]}>
        <Text style={[styles.headerTitle, { color: colors.primary }]}>Agricultural Resources</Text>
      </View>

      <TextInput
        style={[styles.searchInput, { backgroundColor: colors.surfaceContainerLow, borderColor: colors.outline, color: colors.onSurface }]}
        placeholder="Search resources..."
        placeholderTextColor={colors.onSurfaceDisabled}
        value={searchQuery}
        onChangeText={setSearchQuery}
      />

      <ScrollView horizontal={true} showsHorizontalScrollIndicator={false} style={styles.categoryScroll}>
        <TouchableOpacity
          style={[
            styles.categoryChip,
            !category ? styles.categoryChipActive : null,
            { backgroundColor: !category ? colors.primary : colors.surfaceContainerLow },
          ]}
          onPress={() => setCategory(null)}
        >
          <Text
            style={[
              styles.categoryChipText,
              !category ? styles.categoryChipTextActive : null,
              { color: !category ? colors.onPrimary : colors.onSurface },
            ]}
          >
            All
          </Text>
        </TouchableOpacity>
        {categories.map((cat) => (
          <TouchableOpacity
            key={cat}
            style={[
              styles.categoryChip,
              category === cat ? styles.categoryChipActive : null,
              { backgroundColor: category === cat ? colors.primary : colors.surfaceContainerLow },
            ]}
            onPress={() => setCategory(cat)}
          >
            <Text
              style={[
                styles.categoryChipText,
                category === cat ? styles.categoryChipTextActive : null,
                { color: category === cat ? colors.onPrimary : colors.onSurface },
              ]}
            >
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <FlatList
        data={filteredResources}
        keyExtractor={(item) => item.url}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.resourceCard, { backgroundColor: colors.surfaceContainer, shadowColor: colors.shadow }]}
            onPress={() => Linking.openURL(item.url)}
          >
            <View style={styles.resourceHeader}>
              <Text style={[styles.resourceCategory, { color: colors.primary }]}>
                {item.category.charAt(0).toUpperCase() + item.category.slice(1)}
              </Text>
              <Text style={[styles.resourceSource, { color: colors.onSurfaceVariant }]}>{item.source}</Text>
            </View>
            <Text style={[styles.resourceTitle, { color: colors.onSurface }]}>{item.title}</Text>
            <Text style={[styles.resourceDescription, { color: colors.onSurfaceVariant }]}>{item.description}</Text>
            <View style={[styles.resourceFooter, { borderTopColor: colors.outline }]}>
              <Text style={[styles.resourceUrl, { color: colors.primary }]}>{item.url}</Text>
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={[styles.emptyContainer, { backgroundColor: colors.surfaceContainer }]}>
            <Text style={[styles.emptyText, { color: colors.onSurfaceVariant }]}>No resources found</Text>
          </View>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 16,
    borderBottomWidth: 1,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
  },
  searchInput: {
    margin: 16,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    fontSize: 16,
  },
  categoryScroll: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginBottom: 8,
  },
  categoryChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
  },
  categoryChipActive: {},
  categoryChipText: {
    fontSize: 14,
    fontWeight: '500',
  },
  categoryChipTextActive: {
    fontWeight: '600',
  },
  resourceCard: {
    borderRadius: 12,
    padding: 16,
    margin: 16,
    marginBottom: 12,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  resourceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  resourceCategory: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  resourceSource: {
    fontSize: 12,
  },
  resourceTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  resourceDescription: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  resourceFooter: {
    borderTopWidth: 1,
    paddingTop: 8,
  },
  resourceUrl: {
    fontSize: 12,
    fontWeight: '500',
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
  emptyContainer: {
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
  },
});

export default ResourcesList;