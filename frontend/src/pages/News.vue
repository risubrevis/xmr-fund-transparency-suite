<template>
  <div class="space-y-6">
    <!-- Create post card -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 class="text-2xl font-bold text-gray-900 mb-4">News</h2>
      <textarea
        v-model="newPostBody"
        class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-monero-orange focus:outline-none focus:ring-1 focus:ring-monero-orange resize-y min-h-[80px]"
        placeholder="What's new? Share an update with your supporters..."
        maxlength="2048"
        :disabled="submitting"
      />
      <div class="flex items-center justify-between mt-3">
        <span class="text-xs text-gray-400">{{ newPostBody.length }} / 2048</span>
        <Button variant="default" :disabled="!newPostBody.trim() || submitting" @click="handleCreate">
          <div class="flex items-center space-x-1">
            <Loader2 v-if="submitting" :size="14" class="animate-spin" />
            <Send v-else :size="14" />
            <span>{{ submitting ? "Posting..." : "Post" }}</span>
          </div>
        </Button>
      </div>
    </div>

    <!-- Posts list -->
    <div v-if="loading" class="text-center py-8 text-gray-500">Loading posts...</div>
    <div v-else-if="posts.length === 0" class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
      <Newspaper :size="32" class="mx-auto text-gray-300 mb-2" />
      <p class="text-gray-500 text-sm">No posts yet. Share your first update!</p>
    </div>
    <div v-else class="space-y-4">
      <div
        v-for="post in posts"
        :key="post.id"
        class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
      >
        <!-- View mode -->
        <template v-if="editingId !== post.id">
          <p class="text-gray-800 whitespace-pre-wrap text-sm leading-relaxed">{{ post.body }}</p>
          <div class="flex items-center justify-between mt-4">
            <span class="text-xs text-gray-400">{{ formatDate(post.created_at) }}</span>
            <div class="flex items-center space-x-2">
              <Button variant="ghost" size="sm" @click="startEditing(post)">
                <div class="flex items-center space-x-1">
                  <Pencil :size="14" />
                  <span>Edit</span>
                </div>
              </Button>
              <Button variant="ghost" size="sm" class="text-red-500 hover:text-red-600" @click="confirmDelete(post)">
                <div class="flex items-center space-x-1">
                  <Trash2 :size="14" />
                  <span>Delete</span>
                </div>
              </Button>
            </div>
          </div>
        </template>

        <!-- Edit mode -->
        <template v-else>
          <textarea
            v-model="editBody"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-monero-orange focus:outline-none focus:ring-1 focus:ring-monero-orange resize-y min-h-[80px]"
            maxlength="2048"
            :disabled="saving"
          />
          <div class="flex items-center justify-between mt-3">
            <span class="text-xs text-gray-400">{{ editBody.length }} / 2048</span>
            <div class="flex items-center space-x-2">
              <Button variant="outline" size="sm" :disabled="saving" @click="cancelEditing">Cancel</Button>
              <Button variant="default" size="sm" :disabled="!editBody.trim() || saving" @click="handleUpdate(post.id)">
                <div class="flex items-center space-x-1">
                  <Loader2 v-if="saving" :size="14" class="animate-spin" />
                  <Save v-else :size="14" />
                  <span>{{ saving ? "Saving..." : "Save" }}</span>
                </div>
              </Button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <Teleport to="body">
      <div
        v-if="deletingPost"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="deletingPost = null"
      >
        <div class="bg-white rounded-xl p-6 max-w-md mx-4 shadow-xl">
          <div class="flex items-center space-x-2 mb-2">
            <AlertTriangle :size="20" class="text-red-600" />
            <h3 class="text-lg font-bold text-gray-900">Delete Post</h3>
          </div>
          <p class="text-sm text-gray-600 mb-4">
            Are you sure you want to delete this post? This action cannot be undone.
          </p>
          <div class="flex gap-3 justify-end">
            <Button variant="outline" @click="deletingPost = null">Cancel</Button>
            <Button variant="destructive" :disabled="deleting" @click="handleDelete">
              <div class="flex items-center space-x-1">
                <Loader2 v-if="deleting" :size="14" class="animate-spin" />
                <Trash2 v-else :size="14" />
                <span>{{ deleting ? "Deleting..." : "Delete" }}</span>
              </div>
            </Button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import {
  Send,
  Pencil,
  Trash2,
  Save,
  Loader2,
  AlertTriangle,
  Newspaper,
} from "@lucide/vue";
import { Button } from "@/components/ui/button";
import { postsApi, type Post } from "@/lib/api";

const posts = ref<Post[]>([]);
const loading = ref(false);
const submitting = ref(false);
const deleting = ref(false);
const saving = ref(false);

const newPostBody = ref("");
const editingId = ref<string | null>(null);
const editBody = ref("");
const deletingPost = ref<Post | null>(null);

async function loadPosts() {
  loading.value = true;
  try {
    const response = await postsApi.list();
    posts.value = response.data;
  } catch {
    // Posts list is public, errors are unexpected
  } finally {
    loading.value = false;
  }
}

async function handleCreate() {
  if (!newPostBody.value.trim()) return;
  submitting.value = true;
  try {
    const response = await postsApi.create({ body: newPostBody.value.trim() });
    posts.value.unshift(response.data);
    newPostBody.value = "";
  } catch {
    // Error handling via UI state
  } finally {
    submitting.value = false;
  }
}

function startEditing(post: Post) {
  editingId.value = post.id;
  editBody.value = post.body;
}

function cancelEditing() {
  editingId.value = null;
  editBody.value = "";
}

async function handleUpdate(postId: string) {
  if (!editBody.value.trim()) return;
  saving.value = true;
  try {
    const response = await postsApi.update(postId, { body: editBody.value.trim() });
    const index = posts.value.findIndex((p) => p.id === postId);
    if (index !== -1) {
      posts.value[index] = response.data;
    }
    editingId.value = null;
    editBody.value = "";
  } catch {
    // Error handling via UI state
  } finally {
    saving.value = false;
  }
}

function confirmDelete(post: Post) {
  deletingPost.value = post;
}

async function handleDelete() {
  if (!deletingPost.value) return;
  deleting.value = true;
  try {
    await postsApi.delete(deletingPost.value.id);
    posts.value = posts.value.filter((p) => p.id !== deletingPost.value!.id);
    deletingPost.value = null;
  } catch {
    // Error handling via UI state
  } finally {
    deleting.value = false;
  }
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

onMounted(() => {
  loadPosts();
});
</script>
