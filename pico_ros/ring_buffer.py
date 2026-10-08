class RingBuffer:
    def __init__(self, size=10, unit="us", tag="no_tag", warn_full=False):
        self.size = size
        self.data = [0] * size
        self.index = 0       # Próxima posición donde se escribirá
        self.last = 0        # Índice del dato más antiguo
        self.count = 0       # Total de datos agregados históricamente
        self.full = False
        self.unit = unit
        self.tag = tag
        self.warn_full = warn_full

    def append(self, value):
        self.data[self.index] = value
        self.count += 1
        self.index = self.count % self.size

        # Si estamos sobrescribiendo un buffer ya lleno,
        # el dato más antiguo avanza una posición.
        if self.full:
            if self.warn_full:
                print(f"RingBuffer '{self.tag}' lost data: {self.data[self.last]}",self.last,self.index)
            self.last = (self.last + 1) % self.size
        elif self.index==self.last:
            self.full = True

    def pop(self):
        #print("pop0 stored, self.index,rb.last,rb.count,rb.full", self.stored(),self.index,self.last,self.count,self.full,self.data)   # 2

        """Devuelve y elimina el dato más antiguo."""
        if len(self) == 0:
            raise IndexError("pop from empty RingBuffer")

        value = self.data[self.last]

        self.last = (self.last + 1) % self.size

        if self.full:
            self.full = False
        #print("pop1 stored, self.index,rb.last,rb.count,rb.full", self.stored(),self.index,self.last,self.count,self.full,self.data)   # 2

        return value
    
    def pop_all(self):
        """Return all currently stored data and empty the buffer."""

        data = self.get()

        # Empty the current buffer without resetting the historical count.
        self.last = self.index
        self.full = False

        return data  

    def get(self):
        if self.last<self.index:
            return self.data[self.last:self.index]
        elif self.index<self.last:
            return self.data[self.last:] + self.data[:self.index]
        elif self.full:
            return self.data[self.last:] + self.data[:self.index]
        else:
            return self.data[self.last:self.index] #same type of above
            

    def get_disord(self):
        if  self.full:
            return self.data[:]
        else:
            return self.get()

    def __len__(self):
        if self.full:
            return self.size

        return (self.index - self.last) % self.size

    def stats(self):
        data = self.get_disord()

        ret_dic = {
            "len": len(data),
            "count": self.count,
            "unit": self.unit,
            "tag": self.tag,
        }

        if not data:
            return ret_dic

        return ret_dic | {
            "min": min(data),
            "max": max(data),
            "avg": sum(data) / len(data),
        }

    def stored(self):
        """Cantidad de datos actualmente almacenados."""
        return len(self)


if __name__ == "__main__":
    rb = RingBuffer(
        size=3,
        unit="us",
        tag="latency",
        warn_full=True,
    )

    rb.append(10)
    rb.append(20)
    print("stored:", rb.stored())
    print("data:", rb.get())

    rb.append(30)
    print("stored:", rb.stored())
    print("data:", rb.get())

    # El buffer se llena y el aviso se muestra.
    rb.append(40)
    rb.append(50)
    rb.append(60)
    rb.append(70)

    print("data:", rb.get())
    print("count:", rb.count)       # 4: se han agregado 4 datos históricamente
    print("stored:", rb.stored())   # 3: actualmente hay 3 datos

    # Pop elimina el dato más antiguo.
    print("pop:", rb.pop())         # 20
    print("data:", rb.get())        # [30, 40]
    print("stored, rb.index,rb.last,rb.count,rb.full", rb.stored(),rb.index,rb.last,rb.count,rb.full,rb.data)   # 2
    print("pop:", rb.pop())         # 20
    print("data:", rb.get())        # [30, 40]
    print("stored, rb.index,rb.last,rb.count,rb.full", rb.stored(),rb.index,rb.last,rb.count,rb.full)   # 2
    print("pop:", rb.pop())         # 20
    print("data:", rb.get())        # [30, 40]
    print("stored, rb.index,rb.last,rb.count,rb.full", rb.stored(),rb.index,rb.last,rb.count,rb.full)   # 2
    print("pop:", rb.pop())         # 20
    print("data:", rb.get())        # [30, 40]
    print("stored, rb.index,rb.last,rb.count,rb.full", rb.stored(),rb.index,rb.last,rb.count,rb.full)   # 2
