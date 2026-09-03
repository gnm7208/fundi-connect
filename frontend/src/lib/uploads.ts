const CLOUD_NAME = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME as string | undefined
const UPLOAD_PRESET = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET as string | undefined

/** Direct-to-Cloudinary uploads need an unsigned preset; without one we fall back
 *  to letting people paste an image link, so the feature degrades instead of breaking. */
export const uploadsEnabled = Boolean(CLOUD_NAME && UPLOAD_PRESET)

export const MAX_UPLOAD_BYTES = 5 * 1024 * 1024

export class UploadError extends Error {}

export async function uploadImage(file: File): Promise<string> {
  if (!uploadsEnabled) {
    throw new UploadError('Image uploads are not configured. Paste an image link instead.')
  }
  if (!file.type.startsWith('image/')) {
    throw new UploadError('Choose an image file (JPG, PNG or WebP).')
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    throw new UploadError('That image is larger than 5MB. Choose a smaller one.')
  }

  const body = new FormData()
  body.append('file', file)
  body.append('upload_preset', UPLOAD_PRESET!)

  const response = await fetch(`https://api.cloudinary.com/v1_1/${CLOUD_NAME}/image/upload`, {
    method: 'POST',
    body,
  })

  if (!response.ok) {
    throw new UploadError('Upload failed. Check your connection and try again.')
  }

  const payload = await response.json()
  // Ask Cloudinary for a square, face-aware crop so avatars stay consistent.
  return String(payload.secure_url).replace('/upload/', '/upload/c_fill,g_face,w_320,h_320,q_auto/')
}
