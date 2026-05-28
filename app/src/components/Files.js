import React, { useState } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  FlatList, 
  TouchableOpacity, 
  TextInput,
  Alert
} from 'react-native';

export default function Files({ 
  filesList = [], 
  onSelectFile, 
  currentFile, 
  onCreateFile, 
  onCreateFolder, 
  onDeleteItem,
  onRefresh 
}) {
  const [openFolders, setOpenFolders] = useState({});
  const [showInput, setShowInput] = useState(null); // 'file' | 'folder' | null
  const [nameInput, setNameInput] = useState('');

  const toggleFolder = (id) => {
    setOpenFolders(prev => ({
      ...prev,
      [id]: prev[id] === false ? true : false // default is open (true)
    }));
  };

  const handleCreate = () => {
    if (!nameInput.trim()) return;
    
    // Create at root workspace or inside selected folder if selected
    let parentUri = null;
    if (currentFile && currentFile.isDir) {
      parentUri = currentFile.id;
    } else if (currentFile && currentFile.parentId) {
      parentUri = currentFile.parentId;
    }

    if (showInput === 'file') {
      onCreateFile(parentUri, nameInput.trim());
    } else {
      onCreateFolder(parentUri, nameInput.trim());
    }

    setNameInput('');
    setShowInput(null);
  };

  const handleDelete = (item) => {
    Alert.alert(
      'Delete Item',
      `Are you sure you want to delete "${item.name}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: () => onDeleteItem(item.id) }
      ]
    );
  };

  const renderItem = ({ item }) => {
    // Hide files in collapsed folders
    if (item.parentId) {
      let currentParentId = item.parentId;
      while (currentParentId) {
        if (openFolders[currentParentId] === false) {
          return null;
        }
        const parent = filesList.find(f => f.id === currentParentId);
        currentParentId = parent ? parent.parentId : null;
      }
    }

    const isSelected = currentFile && currentFile.id === item.id;
    const paddingLeft = item.parentId ? 24 : 16;
    const isFolderOpen = openFolders[item.id] !== false;

    return (
      <View style={[styles.itemContainer, isSelected && styles.selectedItem]}>
        <TouchableOpacity
          style={[styles.item, { paddingLeft }]}
          onPress={() => {
            if (item.isDir) {
              toggleFolder(item.id);
            }
            onSelectFile(item);
          }}
        >
          <Text style={styles.icon}>
            {item.isDir ? (isFolderOpen ? '📂' : '📁') : '📄'}
          </Text>
          <Text style={[
            styles.itemText, 
            item.isDir && styles.dirText,
            isSelected && styles.selectedItemText
          ]}>
            {item.name}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.deleteBtn}
          onPress={() => handleDelete(item)}
        >
          <Text style={styles.deleteText}>✕</Text>
        </TouchableOpacity>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerTitleRow}>
          <View>
            <Text style={styles.title}>Workspace Explorer</Text>
            <Text style={styles.subtitle}>Real Device Storage</Text>
          </View>
          <TouchableOpacity onPress={onRefresh} style={styles.refreshBtn}>
            <Text style={styles.refreshBtnText}>🔄</Text>
          </TouchableOpacity>
        </View>

        {/* Toolbar */}
        <View style={styles.toolbar}>
          <TouchableOpacity 
            style={[styles.toolBtn, showInput === 'file' && styles.activeToolBtn]}
            onPress={() => setShowInput(showInput === 'file' ? null : 'file')}
          >
            <Text style={styles.toolBtnText}>+ File</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.toolBtn, showInput === 'folder' && styles.activeToolBtn]}
            onPress={() => setShowInput(showInput === 'folder' ? null : 'folder')}
          >
            <Text style={styles.toolBtnText}>+ Folder</Text>
          </TouchableOpacity>
        </View>

        {/* Input box for new items */}
        {showInput && (
          <View style={styles.inputRow}>
            <TextInput
              style={styles.nameInput}
              value={nameInput}
              onChangeText={setNameInput}
              placeholder={showInput === 'file' ? "file_name.py" : "folder_name"}
              placeholderTextColor="#94a3b8"
              autoCapitalize="none"
              autoCorrect={false}
              onSubmitEditing={handleCreate}
              autoFocus
            />
            <TouchableOpacity style={styles.createBtn} onPress={handleCreate}>
              <Text style={styles.createBtnText}>✓</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.cancelBtn} onPress={() => setShowInput(null)}>
              <Text style={styles.cancelBtnText}>✕</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      <FlatList
        data={filesList}
        keyExtractor={item => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.listContent}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f9ff',
  },
  header: {
    padding: 24,
    borderBottomWidth: 1,
    borderBottomColor: '#e0f2fe',
    backgroundColor: '#ffffff',
  },
  headerTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: '900',
    color: '#1f2937',
  },
  subtitle: {
    fontSize: 10,
    color: '#6b7280',
    marginTop: 4,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  refreshBtn: {
    padding: 8,
  },
  refreshBtnText: {
    fontSize: 18,
  },
  toolbar: {
    flexDirection: 'row',
    marginTop: 16,
  },
  toolBtn: {
    backgroundColor: '#f0f9ff',
    borderWidth: 1,
    borderColor: '#e0f2fe',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    marginRight: 10,
  },
  activeToolBtn: {
    backgroundColor: '#e0f2fe',
    borderColor: '#0ea5e9',
  },
  toolBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0ea5e9',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
    borderWidth: 1,
    borderColor: '#e0f2fe',
    borderRadius: 12,
    paddingHorizontal: 12,
    backgroundColor: '#f0f9ff',
  },
  nameInput: {
    flex: 1,
    height: 40,
    color: '#1f2937',
    fontSize: 14,
  },
  createBtn: {
    padding: 8,
    marginLeft: 8,
  },
  createBtnText: {
    fontSize: 16,
    color: '#10b981',
    fontWeight: 'bold',
  },
  cancelBtn: {
    padding: 8,
    marginLeft: 8,
  },
  cancelBtnText: {
    fontSize: 16,
    color: '#ef4444',
    fontWeight: 'bold',
  },
  listContent: {
    paddingVertical: 8,
  },
  itemContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingRight: 16,
  },
  item: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
  selectedItem: {
    backgroundColor: '#e0f2fe',
  },
  icon: {
    fontSize: 16,
    marginRight: 10,
  },
  itemText: {
    fontSize: 16,
    color: '#1f2937',
  },
  selectedItemText: {
    color: '#0ea5e9',
    fontWeight: '700',
  },
  dirText: {
    fontWeight: '600',
  },
  deleteBtn: {
    padding: 8,
  },
  deleteText: {
    color: '#ef4444',
    fontSize: 14,
    fontWeight: 'bold',
  },
});
